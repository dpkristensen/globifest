#/usr/bin/env python
"""
    globifest/Builder.py - globifest

    This script processes package descriptor files and generates output for plugging into another
    build system.

    Copyright 2018, Daniel Kristensen, Garmin Ltd, or its subsidiaries.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this
      list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

    * Neither the name of the copyright holder nor the names of its
      contributors may be used to endorse or promote products derived from
      this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import pathlib
import re

from GlobifestLib import \
    BoundedStatefulParser, \
    Log, \
    Matcher, \
    StatefulParser, \
    StateMachine, \
    Util

from GlobifestLib.StatefulParser import FLAGS as PARSERFLAGS

FILE_LABELS = [
    "aux_files",
    "sources"
    ]

PATH_LABELS = [
    "prv_includes",
    "pub_includes"
    ]

RAW_LABELS = [
    "prv_defines",
    "pub_defines"
    ]

STATE = Util.create_enum(
    "PARSE",
    "COND_IF",
    "COND_ELIF"
    )

COND_STATE = Util.create_enum(
    "PAREN",
    "BRACE",
    )

COND_SUBPARSE_STATE = Util.create_enum(
    "NOT_MET",
    "MET",
    "SATISFIED"
    )

class ManifestParser(StateMachine.Base):
    """
        Encapsulates logic to parse a manifest
    """

    def __init__(self, manifest, configset, debug_mode=False, validate_files=True):
        StateMachine.Base.__init__(self, debug_mode=debug_mode)

        self.configset = configset
        self.manifest = manifest
        self.validate_files = validate_files

        regex_flags = 0
        if Log.Logger.has_level(Log.LEVEL.EXTREME):
            regex_flags = re.DEBUG

        # line regexes, in order of matching
        with Log.CaptureStdout(self, "COMMENT_RE:"):
            self.comment_re = re.compile(";.*", regex_flags)
        with Log.CaptureStdout(self, "DIRECTIVE_RE:"):
            self.directive_re = re.compile(":.*", regex_flags)

        # directive regexes (preceding colon and whitespace stripped off), in order of matching
        with Log.CaptureStdout(self, "CONDITION_IF_RE:"):
            self.condition_if_re = re.compile("if(.*)", regex_flags)
        with Log.CaptureStdout(self, "CONDITION_ELIF_RE:"):
            self.condition_elif_re = re.compile("elif(.*)", regex_flags)
        with Log.CaptureStdout(self, "CONDITION_ELSE_RE:"):
            self.condition_else_re = re.compile("else[ |$](.*)", regex_flags)
        with Log.CaptureStdout(self, "LABEL_RE:"):
            self.label_re = re.compile("([a-z_]+)", regex_flags)

        # Other context variables
        self.label = None

        for label in self.get_labels():
            self.manifest.add_type(label)

    def get_labels(self):
        """
            @return a list of all the labels
        """
        return FILE_LABELS + PATH_LABELS + RAW_LABELS

    def get_manifest(self):
        """Returns the Manifest which is being parsed"""
        return self.manifest

    def log_error(self, err_text):
        """
            Log an error

            @note This does not return
        """
        Log.E("{}: {}".format(self.line_info, err_text))

    def parse(self, line_info):
        """
            Parse a line from a package
        """
        self.line_info = line_info
        line = line_info.get_text()
        Log.D(line)

        if hasattr(self, "cond_parser"):
            # If parsing a conditional, pass the line to the parser
            self.cond_parser.parse(line)
            self._proc_condition_text()
            return

        m = Matcher.new(line)
        if (not line) or (line == ""):
            # empty
            pass
        elif m.is_fullmatch(self.comment_re):
            # Skip comments
            pass
        elif m.is_fullmatch(self.directive_re):
            # Directive: strip off colon to parse
            self._parse_directive(line[1:])
        else:
            # Entry
            self._debug("ENTRY: {}".format(line))
            self._parse_entry(line)

    def _condition_proc_block_change(self):
        """
            When the condition is met, change it to satisfied
        """
        if self.cond_subparse_state._get_state() == COND_SUBPARSE_STATE.MET:
            self.cond_subparse_state._transition(COND_SUBPARSE_STATE.SATISFIED)

    def _condition_proc_expression(self, text):
        """
            Start a conditional statement
        """
        flags = PARSERFLAGS.MULTI_LEVEL
        if self.get_debug_mode():
            flags |= PARSERFLAGS.DEBUG
        self.cond_parser = BoundedStatefulParser.new(text, "(", ")", flags)
        self.cond_parser.link_debug_log(self)

        self._proc_condition_text()

    def _condition_start_if(self, text):
        """
            Start a conditional if statement
        """
        self._transition(STATE.COND_IF)
        self.cond_state = StateMachine.Owned(self, "cond_state")
        self.cond_block = list()
        self._condition_proc_expression(text)

    def _condition_start_elif(self, text):
        """
            Start a conditional elif statement
        """
        if not hasattr(self, "cond_subparse_state"):
            Log.E("elif must be inside a condition block")

        self._transition(STATE.COND_ELIF)
        self.cond_state = StateMachine.Owned(self, "cond_state")
        self._condition_proc_block_change()
        self._condition_proc_expression(text)

    def _parse_directive(self, text):
        """
            Parse directive text
        """
        m = Matcher.new(text.lower())

        if m.is_fullmatch(self.condition_if_re):
            self._debug("IF: {}".format(text))
            self.last_if_type = "if"
            self._condition_start_if(m[1].lstrip())
        elif m.is_fullmatch(self.condition_elif_re):
            self._debug("ELIF: {}".format(text))
            if not hasattr(self, "cond_subparse_state"):
                Log.E("elif must be inside a condition block")
            self.last_if_type = "elif"
            self._condition_start_elif(m[1].lstrip())
        elif m.is_fullmatch(self.condition_else_re):
            self._debug("ELSE: {}".format(text))
            if not hasattr(self, "cond_subparse_state"):
                Log.E("elif must be inside a condition block")
            self._condition_proc_block_change()
            if self.cond_subparse_state != COND_SUBPARSE_STATE.SATISFIED:
                # If the condition has not been satisfied yet, apply these entries
                self.cond_subparse_state._transition(COND_SUBPARSE_STATE.MET)
                self._parse_entry(m[1].lstrip())
        # elif end, reset back to normal processing
        elif m.is_fullmatch(self.label_re):
            self._debug("LABEL: {}".format(text))
            # Label directive (:x)
            self._parse_directive_label(m[1])
        elif not m.found:
            self.log_error("Bad directive '{}'".format(text))

    def _parse_directive_label(self, label):
        """
            Parses a label directive from a package
        """
        if label not in self.get_labels():
            self.log_error("Invalid label name '{}'".format(label))
        else:
            self.label = label

    def _parse_entry(self, entry):
        """
            Parse entry
        """
        if not self.label:
            self.log_error("Missing label for entry {}".format(entry))

        if self.validate_files:
            if self.label in FILE_LABELS:
                path = pathlib.Path(entry)
                if not path.is_file():
                    self.log_error("'{}' is not a file".format(entry))
            elif self.label in PATH_LABELS:
                path = pathlib.Path(entry)
                if not path.is_dir():
                    self.log_error("'{}' is not a directory".format(entry))

        # If this is parsed in a condition context, skip over unmatching entries
        if hasattr(self, "cond_subparse_state"):
            if self.cond_subparse_state._get_state() != COND_SUBPARSE_STATE.MET:
                self._debug("SKIP_ENTRY")
                return

        self._debug("ADD_ENTRY")
        self.manifest.add_entry(self.label, entry)

    def _proc_condition_text(self):
        """
            Process new condition text
        """
        status = self.cond_parser.get_status()

        if self._get_state() not in [STATE.COND_IF, STATE.COND_ELIF]:
            self.log_error("Invalid state")

        # parse until finished or error
        if status == StatefulParser.PARSE_STATUS.ERROR:
            self._debug(self.cond_parser.get_debug_log())
            self.log_error("Malformed condition")
        elif status == StatefulParser.PARSE_STATUS.INCOMPLETE:
            self.cond_block.append(self.line_info)
            return

        parse_state = self.cond_state._get_state()
        if parse_state == COND_STATE.PAREN:
            # Condition expression is completely parsed
            expr = self.cond_parser.get_parsed_text()

            self.last_if_expr_result = self.configset.evaluate(expr)
            self._debug("COND EXPR: '{}' = {}".format(expr, self.last_if_expr_result))

            remaining_text = self.cond_parser.get_remaining_text()

            self.cond_state._transition(COND_STATE.BRACE)
            flags = PARSERFLAGS.MULTI_LEVEL
            if self.get_debug_mode():
                flags |= PARSERFLAGS.DEBUG
            self.cond_parser = BoundedStatefulParser.new(remaining_text, "{", "}", flags)
            self.cond_parser.link_debug_log(self)

            status = self.cond_parser.get_status()
            if status == StatefulParser.PARSE_STATUS.FINISHED:
                # If braces are on one line, process them immediately

                # Replace the original line with just the part inside the braces
                new_text = self.cond_parser.get_parsed_text()
                self.line_info.set_text(new_text)

                self._proc_condition_text()
            elif status == StatefulParser.PARSE_STATUS.INCOMPLETE:
                # Replace the original line with just the part inside the braces
                new_text = self.cond_parser.get_parsed_text()
                self.line_info.set_text(new_text)
                if hasattr(self, "cond_block"):
                    self.cond_block.append(self.line_info)
        elif parse_state == COND_STATE.BRACE:
            self.line_info.set_text(self.cond_parser.get_last_parsed_text())
            self.cond_block.append(self.line_info)

            if self.cond_parser.get_remaining_text() != "":
                self.log_error(
                    "Unexpected text after condition block: {}".format(
                        self.cond_parser.get_remaining_text()
                        )
                    )
            self._transition(STATE.PARSE)
            del self.cond_parser

            # Create a new parser to parse the condition context
            block_parser = new(
                manifest=self.manifest,
                configset=self.configset,
                debug_mode=self.get_debug_mode(),
                validate_files=self.validate_files
                )
            # Set a few additional states for the new parser
            block_parser.label = self.label
            block_parser.cond_subparse_state = StateMachine.Owned(self, "cond_subparse_state")
            if self.last_if_expr_result:
                block_parser.cond_subparse_state._transition(COND_SUBPARSE_STATE.MET)

            self._debug("COND BLOCK:")
            for b in self.cond_block:
                self._debug("  {}".format(b.get_text()))

            block_parser._subparse_condition(self.cond_block, self)
            del self.cond_block
            del self.cond_state
            del self.last_if_expr_result
            self._transition(STATE.PARSE)

    def _subparse_condition(self, cond_block, parent):
        """
            Parse condition context as a sub-parser of another parser

            @note This is run on the subparser object, not the parent parser
        """
        self.link_debug_log(parent)

        self._debug("--SUBCONTEXT COND START--")
        for line_info in cond_block:
            self.parse(line_info)
        self._debug("--SUBCONTEXT COND END--")

new = ManifestParser

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

COND_STATE = Util.create_enum(
    "NOT_MET",
    "MET",
    "SATISFIED"
    )


class Context(object):
    """
        Encapsulates contextual information for a nesting level
    """

    def __init__(self, manifest_parser, prev_context=None, line_info=None, context_parser=None):
        """Initialize the top (file-scope) nesting level"""

        self.manifest_parser = manifest_parser

        if prev_context is None:
            self.label = None
            self.level = 0
            # Top state should never change
            self.cond_state = StateMachine.Owned(
                manifest_parser,
                "***TOP_COND_STATE***",
                init_state=COND_STATE.MET
                )
            self.cond_default_found = False
            self.line_info = "<invalid>"
        else:
            # Derive context from previous
            self.label = prev_context.label
            self.level = prev_context.level + 1
            self.cond_state = StateMachine.Owned(
                manifest_parser,
                "L{} COND_STATE".format(self.level),
                COND_STATE.NOT_MET
                )
            self.cond_default_found = False
            self.line_info = line_info

        # Save the label this context starts with, for conditionals
        self.init_label = self.label

        # Link to the previous context for evaluation
        self.prev_context = prev_context

        self.context_parser = context_parser
        if context_parser:
            self.update_parser()

    def is_condition_met(self):
        """Return True if this context and all parent context conditions are met"""
        ctx = self
        while ctx and (ctx.cond_state._get_state() == COND_STATE.MET):
            ctx = ctx.prev_context

        return ctx is None

    def process_conditional_block_change(self):
        """
            On conditional block change:
            * When the condition is met, change it to satisfied
            * Revert to the original label this context was started with
        """
        if self.cond_state._get_state() == COND_STATE.MET:
            self.cond_state._transition(COND_STATE.SATISFIED)
        if self.label != self.init_label:
            self.label = self.init_label
            self.manifest_parser._debug("LABEL: {}".format(self.init_label))

    def process_conditional_default(self):
        """
            If no conditions have been met, mark it as met now
        """
        if self.cond_state._get_state() == COND_STATE.NOT_MET:
            self.cond_state._transition(COND_STATE.MET)

    def process_line(self, text):
        """
            Process the text in context

            @note Returns True if the line is parsed as part of the context, False if the parser
                should continue parsing it.
        """
        if self.context_parser is None:
            return False

        self.context_parser.parse(text)
        self.update_parser()

        return True

    def update_parser(self):
        """Check the parser for updates"""

        # parse until finished or error
        status = self.context_parser.get_status()
        if status == StatefulParser.PARSE_STATUS.ERROR:
            self.manifest_parser._debug(self.context_parser.get_debug_log())
            self.manifest_parser.log_error("Malformed condition")
        elif status == StatefulParser.PARSE_STATUS.INCOMPLETE:
            return

        # Condition expression is completely parsed
        expr = self.context_parser.get_parsed_text()

        result = self.manifest_parser.configset.evaluate(expr)
        self.manifest_parser._debug("COND EXPR: '{}' = {}".format(expr, result))

        if self.context_parser.get_remaining_text():
            self.manifest_parser.log_error(
                "Unexpected text after expression: '{}'".format(
                    self.context_parser.get_remaining_text()
                    )
                )

        # Done parsing the expression, so delete the parser
        self.context_parser = None

        if result and (self.cond_state._get_state() == COND_STATE.NOT_MET):
            self.cond_state._transition(COND_STATE.MET)

class ManifestParser(Log.Debuggable):
    """
        Encapsulates logic to parse a manifest
    """

    def __init__(self, manifest, configset, debug_mode=False, validate_files=True):
        Log.Debuggable.__init__(self, debug_mode=debug_mode)

        self.configset = configset
        self.manifest = manifest
        self.validate_files = validate_files
        self.line_info = None

        # Always has a context
        top_context = Context(manifest_parser=self)
        self.context_stack = [top_context]

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
            self.condition_else_re = re.compile("else$", regex_flags)
        with Log.CaptureStdout(self, "CONDITION_END_RE:"):
            self.condition_end_re = re.compile("end$", regex_flags)
        with Log.CaptureStdout(self, "LABEL_RE:"):
            self.label_re = re.compile("([a-z_]+)", regex_flags)

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
        self._debug("PARSE: {}".format(line))

        cur_context = self.context_stack[-1]
        if cur_context.process_line(line):
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
            self._parse_entry(line)

    def parse_end(self):
        if not self.context_stack:
            self.log_error("Invalid post-parsing state")
        elif len(self.context_stack) != 1:
            self.log_error(
                "Unterminated block started at {}".format(self.context_stack[-1].line_info)
                )

    def _condition_end(self):
        """
            End a conditional statement
        """
        if (not self.context_stack) or (self.context_stack[-1].level == 0):
            self.log_error("end must be at the end of a condition block")

        self.context_stack.pop(-1)

    def _condition_start_if(self, text):
        """
            Start a conditional statement

            Push a new context onto the stack and start looking for an expression
        """
        new_context = Context(
                manifest_parser=self,
                prev_context=self.context_stack[-1],
                line_info=self.line_info,
                context_parser=self._create_paren_parser(text)
            )
        self.context_stack.append(new_context)

    def _condition_start_elif(self, text):
        """
            Start an elif block in a conditional statement
        """
        if (not self.context_stack) or (self.context_stack[-1].level == 0):
            self.log_error("elif must be inside a condition block")

        cur_context = self.context_stack[-1]
        cur_context.process_conditional_block_change()
        if cur_context.context_parser is not None:
            self.log_error("Expected end of expression")
        
        cur_context.context_parser = self._create_paren_parser(text)
        cur_context.update_parser()

    def _condition_start_else(self):
        """
            Start an else block in a conditional statement
        """
        if (not self.context_stack) or (self.context_stack[-1].level == 0):
            self.log_error("else must be inside a condition block")

        cur_context = self.context_stack[-1]
        cur_context.process_conditional_block_change()
        cur_context.process_conditional_default()

    def _create_paren_parser(self, text):
        """Return a parser for finding a bounded set of parentheses"""
        flags = PARSERFLAGS.MULTI_LEVEL
        if self.get_debug_mode():
            flags |= PARSERFLAGS.DEBUG
        paren_parser = BoundedStatefulParser.new(text, "(", ")", flags)
        paren_parser.link_debug_log(self)
        return paren_parser

    def _parse_directive(self, text):
        """
            Parse directive text
        """
        m = Matcher.new(text.lower())

        if m.is_fullmatch(self.condition_if_re):
            self._debug("IF: {}".format(m[1]))
            self._condition_start_if(m[1].lstrip())
        elif m.is_fullmatch(self.condition_elif_re):
            self._debug("ELIF: {}".format(m[1]))
            self._condition_start_elif(m[1].lstrip())
        elif m.is_fullmatch(self.condition_else_re):
            self._debug("ELSE")
            self._condition_start_else()
        elif m.is_fullmatch(self.condition_end_re):
            self._debug("END")
            self._condition_end()
        elif m.is_fullmatch(self.label_re):
            self._debug("LABEL: {}".format(m[1]))
            # Label directive (:x)
            self._parse_directive_label(m[1])
        elif not m.found:
            self.log_error("Bad directive '{}'".format(text))

    def _parse_directive_label(self, label):
        """
            Parses a label directive from a package
        """
        cur_context = self.context_stack[-1]
        if label not in self.get_labels():
            self.log_error("Invalid label name '{}'".format(label))
        else:
            cur_context.label = label

    def _parse_entry(self, entry):
        """
            Parse entry
        """
        cur_context = self.context_stack[-1]
        if not cur_context.label:
            self.log_error("Missing label for entry {}".format(entry))

        if self.validate_files:
            if cur_context.label in FILE_LABELS:
                path = pathlib.Path(entry)
                if not path.is_file():
                    self.log_error("'{}' is not a file".format(entry))
            elif cur_context.label in PATH_LABELS:
                path = pathlib.Path(entry)
                if not path.is_dir():
                    self.log_error("'{}' is not a directory".format(entry))

        # If this is parsed in a condition context, skip over unmatching entries
        if not cur_context.is_condition_met():
            self._debug("SKIP_ENTRY: {}".format(entry))
            return

        self._debug("ADD_ENTRY: {}".format(entry))
        self.manifest.add_entry(cur_context.label, entry)

new = ManifestParser

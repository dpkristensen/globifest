#/usr/bin/env python
"""
    globifest/ManifestParser.py - globifest

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

import glob
import os
import pathlib
import re

from GlobifestLib import \
    BoundedStatefulParser, \
    Generators, \
    LineReader, \
    Log, \
    Matcher, \
    Settings, \
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

PUBLIC_LABELS = [
    "pub_includes",
    "pub_defines"
    ]

COND_STATE = Util.create_enum(
    "NOT_MET",
    "MET",
    "SATISFIED"
    )

class ConfigsOnly(Settings.Settings):
    """
        Class to use when only reading configs
    """

    def get_value(self, name):
        """Stub; should never be called"""
        Log.E("Internal error: cannot return value", err_type=Log.ERROR.RUNTIME)

    def has_value(self, name):
        """Stub; returns True"""
        return True

    def evaluate(self, expr):
        """Stub; returns True"""
        return True

class Context(object):
    """
        Base class for parsing contexts
    """

    CTYPE = Util.create_enum(
        "CONDITION",
        "CONFIG"
        )

    def __init__(self, manifest_parser, prev_context, line_info, ctype):
        """Initializes shared context info"""

        self.manifest_parser = manifest_parser
        self.ctype = ctype

        if prev_context is None:
            self.level = 0
            self.line_info = "<invalid>"
        else:
            # Derive context from previous
            self.level = prev_context.level + 1
            self.line_info = line_info

        # Link to the previous context
        self.prev_context = prev_context

    def get_ctype(self):
        """Returns the context type"""
        return self.ctype

    def has_parameters(self):
        """Returns whether this type of context has parameters"""
        if self.ctype == Context.CTYPE.CONDITION:
            return False

        return True

class ConditionContext(Context):
    """
        Encapsulates contextual information for a nesting level
    """

    def __init__(self, manifest_parser, prev_context=None, line_info=None, context_parser=None):
        """Initialize the top (file-scope) nesting level"""
        Context.__init__(self, manifest_parser, prev_context, line_info, Context.CTYPE.CONDITION)

        if prev_context is None:
            self.label = None
            # Top state should never change
            self.cond_state = StateMachine.Owned(
                manifest_parser,
                "***TOP_COND_STATE***",
                init_state=COND_STATE.MET
                )
            self.cond_default_found = False
        else:
            # Derive context from previous
            self.label = prev_context.label
            self.cond_state = StateMachine.Owned(
                manifest_parser,
                "L{} COND_STATE".format(self.level),
                COND_STATE.NOT_MET
                )
            self.cond_default_found = False

        # Save the label this context starts with, for conditionals
        self.init_label = self.label

        self.context_parser = context_parser
        if context_parser:
            self.update_parser()

    def is_condition_met(self):
        """Return True if this context and all parent context conditions are met"""
        ctx = self
        while ctx and (ctx.cond_state.get_state() == COND_STATE.MET):
            ctx = ctx.prev_context

        return ctx is None

    def process_conditional_block_change(self):
        """
            On conditional block change:
            * When the condition is met, change it to satisfied
            * Revert to the original label this context was started with
        """
        if self.cond_state.get_state() == COND_STATE.MET:
            self.cond_state.transition(COND_STATE.SATISFIED)
        if self.label != self.init_label:
            self.label = self.init_label
            self.manifest_parser.debug("LABEL: {}".format(self.init_label))

    def process_conditional_default(self):
        """
            If no conditions have been met, mark it as met now
        """
        if self.cond_state.get_state() == COND_STATE.NOT_MET:
            self.cond_state.transition(COND_STATE.MET)

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
            self.manifest_parser.debug(self.context_parser.get_debug_log())
            self.manifest_parser.log_error("Malformed condition")
        elif status == StatefulParser.PARSE_STATUS.INCOMPLETE:
            return

        # Condition expression is completely parsed
        expr = self.context_parser.get_parsed_text()

        try:
            result = self.manifest_parser.settings.evaluate(expr)
        except Log.GlobifestException:
            # Add line context to this error
            self.manifest_parser.log_error("Failed to evaluate expression")
        self.manifest_parser.debug("COND EXPR: '{}' = {}".format(expr, result))

        if self.context_parser.get_remaining_text():
            self.manifest_parser.log_error(
                "Unexpected text after expression: '{}'".format(
                    self.context_parser.get_remaining_text()
                    )
                )

        # Done parsing the expression, so delete the parser
        self.context_parser = None

        if result and (self.cond_state.get_state() == COND_STATE.NOT_MET):
            self.cond_state.transition(COND_STATE.MET)

# Map of unique config element strings to Context.ctx member names in no particular order
CONFIG_ELEMENTS = Util.Container(
    # "generate" is not unique, so not present in this list
    # "formatter" can be overwritten, so not present in this list
    definition="definition"
    )

class ParameterContext(Context):
    """
        Encapsulates contextual information for a parameterized section
    """

    def __init__(self, manifest_parser, ctype, prev_context=None, line_info=None, ctx=None):
        """Initialize the context"""
        # Set up context-specific values
        self.ctx = ctx or Util.Container(ctype=None)

        Context.__init__(self, manifest_parser, prev_context, line_info, ctype)

    def is_complete(self):
        """Return whether context has all required information"""
        if self.ctype == Context.CTYPE.CONFIG:
            self.validate_config()
        else:
            assert self.ctype is not None
            return False
        return True

    def is_unique_element(self, elements, name):
        """Return whether name is in elements, and is not already stored in ctx"""

        if name not in elements.keys():
            self.manifest_parser.log_error("Invalid parameter: {}".format(name))

        if self.ctx[elements[name]] is not None:
            self.manifest_parser.log_error("Redefinition of {}".format(name))

        return True

    def process_line(self, _text):
        """Stub, returns False"""
        # This is called too early to be used to process parameters
        return False

    def process_param(self, name, value):
        """Process a parameter in context"""
        if self.ctype == Context.CTYPE.CONFIG:
            self.process_param_config(name, value)

    def process_param_config(self, name, value):
        """Process a config parameter"""
        if not value:
            self.manifest_parser.log_error("Bad parameter: {}".format(value))

        if name == "generate":
            token = value.split(" ", 1)
            if len(token) != 2:
                self.manifest_parser.log_error("generate requires a format and filename")
            generator = Generators.factory(
                gen_format=token[0],
                filename=token[1],
                formatter=self.ctx.formatter
            )

            if generator is None:
                self.manifest_parser.log_error("Invalid format '{}'".format(token[0]))
            self.ctx.generators.append(generator)
        elif name == "formatter":
            self.ctx.formatter = value
        elif self.is_unique_element(CONFIG_ELEMENTS, name):
            # No additional validation required for these elements
            self.ctx[CONFIG_ELEMENTS[name]] = value
        else:
            self.manifest_parser.debug("not found: {}".format(name))

    def validate_config(self):
        """Validate the final state of a config context"""
        # Validate required fields
        if not self.ctx.definition:
            self.manifest_parser.log_error("Config requires a definition file")

class ManifestParser(Log.Debuggable):
    """
        Encapsulates logic to parse a manifest
    """

    def __init__(self, manifest, settings, debug_mode=False, validate_files=True):
        Log.Debuggable.__init__(self, debug_mode=debug_mode)

        self.settings = settings
        self.manifest = manifest
        self.validate_files = validate_files
        self.line_info = None
        self.pkg_root = manifest.get_root()

        # Always has a context
        top_context = ConditionContext(manifest_parser=self)
        self.context_stack = [top_context]

        regex_flags = 0
        if Log.Logger.has_level(Log.LEVEL.EXTREME):
            regex_flags = re.DEBUG

        # line regexes, in order of matching
        with Log.CaptureStdout(self, "COMMENT_RE:"):
            self.comment_re = re.compile("[;#].*", regex_flags)
        with Log.CaptureStdout(self, "DIRECTIVE_RE:"):
            self.directive_re = re.compile(":.*", regex_flags)
        with Log.CaptureStdout(self, "PARAMETER_RE:"):
            self.parameter_re = re.compile("([a-z]+)[ \t]+(.*)$", regex_flags)

        # directive regexes (preceding colon and whitespace stripped off), in order of matching
        with Log.CaptureStdout(self, "CONFIG_RE:"):
            self.config_re = re.compile("config", regex_flags)
        with Log.CaptureStdout(self, "CONDITION_IF_RE:"):
            self.condition_if_re = re.compile("if(.*)", regex_flags)
        with Log.CaptureStdout(self, "CONDITION_ELIF_RE:"):
            self.condition_elif_re = re.compile("elif(.*)", regex_flags)
        with Log.CaptureStdout(self, "CONDITION_ELSE_RE:"):
            self.condition_else_re = re.compile("else$", regex_flags)
        with Log.CaptureStdout(self, "BLOCK_END_RE:"):
            self.block_end_re = re.compile("end$", regex_flags)
        with Log.CaptureStdout(self, "INCLUDE_RE:"):
            self.include_re = re.compile("include[ ]+(.*)", regex_flags)
        with Log.CaptureStdout(self, "LABEL_RE:"):
            self.label_re = re.compile("([a-z_]+)", regex_flags)

        for label in self.get_labels():
            self.manifest.add_type(label)

    def get_labels(self):
        """
            @return a list of all the labels
        """
        return FILE_LABELS + PATH_LABELS + RAW_LABELS

    def get_target(self):
        """Returns the target Manifest which is being parsed"""
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
        self.debug("PARSE: {}".format(line))

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
        elif cur_context.has_parameters():
            if m.is_fullmatch(self.parameter_re):
                #pylint: disable=E1101
                cur_context.process_param(m[1], m[2])
            else:
                self.log_error("Malformed parameter: {}".format(line))
        else:
            # Entry
            self._parse_entry(line)

    def parse_end(self):
        """
            End parsing of the manifest
        """
        if not self.context_stack:
            self.log_error("Invalid post-parsing state")
        elif len(self.context_stack) != 1:
            self.log_error(
                "Unterminated block started at {}".format(self.context_stack[-1].line_info)
                )

    def _block_end(self):
        """
            End a block statement (parameterized context)
        """
        if (not self.context_stack) or (self.context_stack[-1].level == 0):
            self.log_error("end must be at the end of a block")

        cur_context = self.context_stack[-1]
        #pylint: disable=E1101
        if not cur_context.is_complete():
            self.log_error("Incomplete block started at {}".format(cur_context.line_info))

        ctype = cur_context.get_ctype()
        if ctype == Context.CTYPE.CONFIG:
            self._config_end(cur_context)
        else:
            assert ctype is not None

        self.context_stack.pop(-1)

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
        new_context = ConditionContext(
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

    def _config_end(self, context):
        """End a config block"""
        self.manifest.add_config(Util.Container(
            definition=context.ctx.definition,
            generators=context.ctx.generators
        ))

    def _config_start(self):
        """Start a config block"""
        config_context = ParameterContext(
            manifest_parser=self,
            ctype=Context.CTYPE.CONFIG,
            prev_context=self.context_stack[-1],
            line_info=self.line_info,
            ctx=Util.Container(
                definition=None,
                formatter=None,
                generators=[]
            )
        )
        self.context_stack.append(config_context)

    def _create_paren_parser(self, text):
        """Return a parser for finding a bounded set of parentheses"""
        flags = PARSERFLAGS.MULTI_LEVEL
        if self.get_debug_mode():
            flags |= PARSERFLAGS.DEBUG
        paren_parser = BoundedStatefulParser.new(text, "(", ")", flags)
        paren_parser.link_debug_log(self)
        return paren_parser

    def _include_file(self, filename):
        """
            Include the contents of another file as if it was directly placed in this file
        """
        abs_filename = Util.get_abs_path(filename, self.pkg_root)

        if not self.validate_files:
            # For testing, just add the include file as a source
            self.debug("ADD_AUX: {}".format(abs_filename))
            self.manifest.add_entry("aux_files", abs_filename)
            return

        # Save the package root so that files paths can be relative to the included file
        old_pkg_root = self.pkg_root
        self.pkg_root = os.path.dirname(abs_filename)

        # Read the file using this object as the parser
        reader = LineReader.new(self, do_end=False)
        reader.read_file_by_name(abs_filename)

        # Restore the original package root
        self.pkg_root = old_pkg_root

    def _parse_directive(self, text):
        """
            Parse directive text
        """
        if not self.context_stack:
            self.log_error("Unknown error")
            return

        m = Matcher.new(text)
        cur_context = self.context_stack[-1]

        if cur_context.has_parameters():
            ok = self._parse_directive_parameter_content(m)
        else:
            ok = self._parse_directive_entry_content(m)

        if not ok:
            self.log_error("Bad directive '{}'".format(text))

    def _parse_directive_entry_content(self, matcher):
        """
            Parse directives with entry content (as opposed to parameter content)

            Returns whether the line was parsed successfully
        """
        m = matcher
        if m.is_fullmatch(self.config_re):
            self.debug("CONFIG")
            self._config_start()
        elif m.is_fullmatch(self.condition_if_re):
            self.debug("IF: {}".format(m[1]))
            self._condition_start_if(m[1].lstrip())
        elif m.is_fullmatch(self.condition_elif_re):
            self.debug("ELIF: {}".format(m[1]))
            self._condition_start_elif(m[1].lstrip())
        elif m.is_fullmatch(self.condition_else_re):
            self.debug("ELSE")
            self._condition_start_else()
        elif m.is_fullmatch(self.block_end_re):
            self.debug("END")
            self._condition_end()
        elif m.is_fullmatch(self.include_re):
            self.debug("INCLUDE: {}".format(m[1]))
            self._include_file(m[1])
        elif m.is_fullmatch(self.label_re):
            self.debug("LABEL: {}".format(m[1]))
            # Label directive (:x)
            self._parse_directive_label(m[1])
        else:
            return False

        return True

    def _parse_directive_parameter_content(self, matcher):
        """
            Parse directives with parameter content (as opposed to entry content)

            Returns whether the line was parsed successfully
        """
        m = matcher
        if m.is_fullmatch(self.block_end_re):
            self.debug("END")
            self._block_end()
        else:
            return False

        return True

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
            # When validating files (i.e., a real build), change to absolute path
            entry = Util.get_abs_path(entry, self.pkg_root)
            if cur_context.label in FILE_LABELS:
                path = None
                for f in glob.iglob(entry):
                    path = pathlib.Path(f)
                    if not path.is_file():
                        self.log_error("'{}' is not a file".format(f))
                if path is None:
                    self.log_error("'{}' does not match any files".format(entry))
            elif cur_context.label in PATH_LABELS:
                path = pathlib.Path(entry)
                if not path.is_dir():
                    self.log_error("'{}' is not a directory".format(entry))

        # If this is parsed in a condition context, skip over unmatching entries
        if not cur_context.is_condition_met():
            self.debug("SKIP_ENTRY: {}".format(entry))
            return

        if (cur_context.label in FILE_LABELS) and (self.validate_files):
            for f in glob.iglob(entry):
                self.debug("ADD_FILE: {}".format(f))
                self.manifest.add_entry(cur_context.label, f)
        else:
            self.debug("ADD_ENTRY: {}".format(entry))
            self.manifest.add_entry(cur_context.label, entry)


new = ManifestParser

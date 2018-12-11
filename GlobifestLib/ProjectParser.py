#/usr/bin/env python
"""
    globifest/ProjectParser.py - globifest

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

import re

from GlobifestLib import \
    Log, \
    Matcher, \
    Util

IDENTIFIER_NAME = "[a-zA-Z0-9_]+"

# Map of unique Layer element strings to Context.ctx member names in no particular order
LAYER_ELEMENTS = Util.Container(
    # "variant" is not unique, so not present in this list
    prefix="prefix",
    suffix="suffix"
    )

class Context(object):
    """
        Encapsulates contextual information for a nesting level
    """

    CTYPE = Util.create_enum(
        "LAYER",
        "PROJECT"
        )

    def __init__(self, config_parser, prev_context=None, line_info=None, ctx=None):
        """Initialize the top (file-scope) nesting level"""

        self.config_parser = config_parser

        if prev_context is None:
            self.level = 0
            self.line_info = "<invalid>"
        else:
            # Derive context from previous
            self.level = prev_context.level + 1
            self.line_info = line_info

        # Link to the previous context
        self.prev_context = prev_context

        # Set up context-specific values
        self.ctx = ctx or Util.Container(ctype=None)
        assert hasattr(self.ctx, "ctype")

    def get_ctype(self):
        """Return the context type"""
        return self.ctx.ctype

    def is_complete(self):
        """Return whether context has all required information"""
        if self.ctx.ctype == Context.CTYPE.PROJECT:
            self.validate_project()
        elif self.ctx.ctype == Context.CTYPE.LAYER:
            self.validate_layer()
        else:
            assert self.ctx.ctype is not None
            return False
        return True

    def is_unique_element(self, elements, name):
        """Return whether name is in elements, and is not already stored in ctx"""

        if name not in elements.keys():
            self.config_parser.log_error("Invalid parameter: {}".format(name))

        if self.ctx[elements[name]] is not None:
            self.config_parser.log_error("Redefinition of {}".format(name))

        return True

    def process_param(self, name, value):
        """Process a parameter in context"""
        if self.ctx.ctype == Context.CTYPE.PROJECT:
            self.config_parser.log_error("Projects have no parameters")
        if self.ctx.ctype == Context.CTYPE.LAYER:
            self.process_param_layer(name, value)

    def process_param_layer(self, name, value):
        """Process a layer parameter"""
        if not value:
            self.config_parser.log_error("Bad parameter: {}".format(value))

        if name == "variant":
            if re.fullmatch(IDENTIFIER_NAME, value):
                self.ctx.variants.append(value)
            else:
                self.config_parser.log_error("Invalid identifier: {}".format(value))
        elif self.is_unique_element(LAYER_ELEMENTS, name):
            # No additional validation required for these elements
            self.ctx[LAYER_ELEMENTS[name]] = value
        else:
            self.config_parser.debug("not found: {}".format(name))

    def validate_layer(self):
        """Validate the final state of a layer context"""
        # Set defaults
        if not self.ctx.prefix:
            self.ctx.prefix = self.prev_context.ctx.prj_name + "_" + self.ctx.layer_name + "_"
        if not self.ctx.suffix:
            self.ctx.suffix = ".cfg"

        # Validate required fields
        if not self.ctx.variants:
            self.config_parser.log_error("Layer {} has no variants".format(self.ctx.layer_name))

    def validate_project(self):
        """Validate the final state of a project context"""
        # Validate required fields
        if not self.ctx.prj_name:
            self.config_parser.log_error("Missing project name")

class ProjectParser(Log.Debuggable):
    """
        Encapsulates logic to parse a configuration file
    """

    def __init__(self, project, debug_mode=False):
        Log.Debuggable.__init__(self, debug_mode=debug_mode)

        self.config_project = project
        self.line_info = None

        # Always has a context
        top_context = Context(config_parser=self)
        self.context_stack = [top_context]

        regex_flags = 0
        if Log.Logger.has_level(Log.LEVEL.EXTREME):
            regex_flags = re.DEBUG

        # line regexes, in order of matching
        with Log.CaptureStdout(self, "COMMENT_RE:"):
            self.comment_re = re.compile("[;#].*", regex_flags)
        with Log.CaptureStdout(self, "DIRECTIVE_RE:"):
            self.directive_re = re.compile(":.*", regex_flags)

        # directive regexes (preceding colon and whitespace stripped off), in order of matching
        with Log.CaptureStdout(self, "BLOCK_END_RE:"):
            self.block_end_re = re.compile("end$", regex_flags)
        with Log.CaptureStdout(self, "PROJECT_RE:"):
            self.project_re = re.compile(
                "project[ \t]+(.+)$",
                regex_flags
                )
        with Log.CaptureStdout(self, "LAYER_RE:"):
            self.layer_re = re.compile(
                "layer[ \t]+(.+)$",
                regex_flags
                )

        # Block parameter regex
        with Log.CaptureStdout(self, "BLOCK_PARAM_RE::"):
            self.param_re = re.compile("(" + IDENTIFIER_NAME + ")[ \t]+(.+)", regex_flags)

    def get_target(self):
        """Returns the target Project which is being parsed"""
        return self.config_project

    def log_error(self, err_text):
        """
            Log an error

            @note This does not return
        """
        Log.E("{}: {}".format(self.line_info, err_text))

    def parse(self, line_info):
        """
            Parse a line from a file
        """
        self.line_info = line_info
        line = line_info.get_text()
        self.debug("PARSE: {}".format(line))

        cur_context = self.context_stack[-1]

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
        elif m.is_fullmatch(self.param_re):
            cur_context.process_param(m[1], m[2].rstrip())
        else:
            self.log_error("Bad grammar: cannot parse {}".format(line_info))

    def parse_end(self):
        """
            End parsing of the config file
        """
        if not self.context_stack:
            self.log_error("Invalid post-parsing state")
        elif len(self.context_stack) != 1:
            self.log_error(
                "Unterminated block started at {}".format(self.context_stack[-1].line_info)
                )

    def _block_end(self):
        """
            End a block statement
        """
        if (not self.context_stack) or (self.context_stack[-1].level == 0):
            self.log_error("end must be at the end of a block")

        cur_context = self.context_stack[-1]
        if not cur_context.is_complete():
            self.log_error("Incomplete block started at {}".format(cur_context.line_info))

        ctype = cur_context.get_ctype()
        if ctype == Context.CTYPE.PROJECT:
            self._project_end(cur_context)
        elif ctype == Context.CTYPE.LAYER:
            self._layer_end(cur_context)
        else:
            assert ctype is not None

        self.context_stack.pop(-1)

    def _layer_end(self, context):
        """
            End a layer block

            Save the layer
        """
        self.config_project.add_layer(context.ctx.layer_name)
        for variant in context.ctx.variants:
            self.config_project.add_variant(
                context.ctx.layer_name,
                variant,
                context.ctx.prefix + variant + context.ctx.suffix # Filename
                )

    def _layer_start(self, name):
        """
            Start a layer block

            Push a new context onto the stack with CTYPE.LAYER.
        """
        cur_context = self.context_stack[-1]
        ctype = cur_context.get_ctype()
        if ctype not in [Context.CTYPE.PROJECT]:
            self.log_error("layer is not allowed in this scope")

        new_context = Context(
            config_parser=self,
            prev_context=cur_context,
            line_info=self.line_info,
            ctx=Util.Container(
                ctype=Context.CTYPE.LAYER,
                layer_name=name,
                variants=[], # Initially empty list
                prefix=None,
                suffix=None
                )
            )
        self.debug("  {}".format(name))
        self.context_stack.append(new_context)

    def _project_end(self, context):
        """
            End a project block

            Save the project
        """
        if self.config_project.get_name() is not None:
            self.log_error("Cannot redefine project")

        self.config_project.set_name(context.ctx.prj_name)

        assert self.config_project is not None

    def _project_start(self, name):
        """
            Start a project block

            Push a new context onto the stack with CTYPE.PROJECT.
        """
        cur_context = self.context_stack[-1]
        ctype = cur_context.get_ctype()
        if ctype not in [None]:
            self.log_error("project is not allowed in this scope")

        if self.config_project.get_name() is not None:
            self.log_error("Cannot define multiple projects")

        new_context = Context(
            config_parser=self,
            prev_context=cur_context,
            line_info=self.line_info,
            ctx=Util.Container(
                ctype=Context.CTYPE.PROJECT,
                prj_name=name
                )
            )
        self.debug("  {}".format(name))
        self.context_stack.append(new_context)

    def _parse_directive(self, text):
        """
            Parse directive text
        """
        m = Matcher.new(text)

        if m.is_fullmatch(self.layer_re):
            self.debug("LAYER: {}".format(m[1]))
            self._layer_start(m[1])
        elif m.is_fullmatch(self.project_re):
            self.debug("PROJECT: {}".format(m[1]))
            self._project_start(m[1])
        elif m.is_fullmatch(self.block_end_re):
            self.debug("END")
            self._block_end()
        elif not m.found:
            self.log_error("Bad directive '{}'".format(text))

new = ProjectParser

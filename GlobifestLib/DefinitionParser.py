#/usr/bin/env python
"""
    globifest/DefinitionParser.py - globifest

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

import os
import re

from GlobifestLib import \
    DefTree, \
    LineReader, \
    Log, \
    Matcher, \
    Util

# Map of DefTree element strings to Context.ctx member names in no particular order
CONFIG_ELEMENTS = Util.Container(
    default="default",
    description="desc",
    title="title",
    type="ptype",
    count="cnt_id"
    )

# Map of menu element strings to Context.ctx member names in no particular order
MENU_ELEMENTS = Util.Container(
    description="mdesc"
    )

class Context(object):
    """
        Encapsulates contextual information for a nesting level
    """

    CTYPE = Util.create_enum(
        "CONFIG",
        "MENU"
        )

    def __init__(self, def_parser, prev_context=None, line_info=None, ctx=None):
        """Initialize the top (file-scope) nesting level"""

        self.def_parser = def_parser

        if prev_context is None:
            self.level = 0
            self.line_info = "<invalid>"
            self.scope_path = "/"
        else:
            # Derive context from previous
            self.level = prev_context.level + 1
            self.line_info = line_info
            self.scope_path = None

        # Link to the previous context
        self.prev_context = prev_context

        # Set up context-specific values
        self.ctx = ctx or Util.Container(ctype=None)
        assert hasattr(self.ctx, "ctype")

    def get_ctype(self):
        """Return the context type"""
        return self.ctx.ctype

    def get_scope_path(self):
        """Return the path of this scope"""
        if self.scope_path is None:
            # No scope specified, use parent path
            return self.prev_context.get_scope_path()

        if self.scope_path[0] == "/":
            # Absolute path
            return self.scope_path

        # Relative path
        return self.prev_context.get_scope_path() + self.scope_path + "/"

    def is_complete(self):
        """Return whether context has all required information"""
        if self.ctx.ctype == Context.CTYPE.CONFIG:
            self.validate_config()
        elif self.ctx.ctype == Context.CTYPE.MENU:
            pass # Nothing to do
        else:
            assert self.ctx.ctype is not None
            return False
        return True

    def is_unique_element(self, elements, name):
        """Return whether name is in elements, and is not already stored in ctx"""

        if name not in elements.keys():
            self.def_parser.log_error("Invalid parameter: {}".format(name))

        if self.ctx[elements[name]] is not None:
            self.def_parser.log_error("Redefinition of {}".format(name))

        return True

    def process_param(self, name, value):
        """Process a parameter in context"""
        if self.ctx.ctype == Context.CTYPE.CONFIG:
            self.process_param_config(name, value)
        elif self.ctx.ctype == Context.CTYPE.MENU:
            self.process_param_menu(name, value)

    def process_param_config(self, name, value):
        """Process a config parameter"""
        if not value:
            self.def_parser.log_error("Bad parameter: {}".format(value))

        if name == "menu":
            # The menu parameter requires special handling, since it overwrites the scope_path
            if self.scope_path is not None:
                self.def_parser.log_error("Redefinition of menu")
            else:
                self.scope_path = value
        elif name == "choice":
            ventry = value.split(" ", 1)
            v_id = ventry[0]
            try:
                v_text = ventry[1]
            except IndexError:
                v_text = "\"{}\"".format(v_id)
            self.ctx.vlist.append(Util.Container(
                id=v_id,
                text=v_text
                ))
        elif self.is_unique_element(CONFIG_ELEMENTS, name):
            if name == "type":
                self.ctx.ptype = DefTree.validate_type(value)
                if self.ctx.ptype is None:
                    self.def_parser.log_error("Invalid type: {}".format(value))
            elif name == "default":
                if self.ctx.ptype is None:
                    self.def_parser.log_error("default must appear after type")

                self.ctx.default = DefTree.validate_value(self.ctx.ptype, value)
                if self.ctx.default is None:
                    self.def_parser.log_error("Invalid value: {}".format(value))
            else:
                # No additional validation required for other elements
                self.ctx[CONFIG_ELEMENTS[name]] = value
        else:
            self.def_parser.debug("not found: {}".format(name))

    def process_param_menu(self, name, value):
        """Process a menu parameter"""
        if not value:
            self.def_parser.log_error("Bad parameter: {}".format(value))

        if self.is_unique_element(MENU_ELEMENTS, name):
            # No additional validation required for elements
            self.ctx[MENU_ELEMENTS[name]] = value
        else:
            self.def_parser.debug("not found: {}".format(name))

    def validate_config(self):
        """Validate the final state of a config context"""
        # Set defaults
        if self.ctx.title is None:
            self.ctx.title = ""
        if self.ctx.desc is None:
            self.ctx.desc = ""

        # Validate required fields
        if not self.ctx.id:
            self.def_parser.log_error("Missing config ID")
        elif self.ctx.ptype is None:
            self.def_parser.log_error("Missing type for config {}".format(self.ctx.id))

        # Validate type-specific items
        if self.ctx.ptype == DefTree.PARAM_TYPE.ENUM:
            if not self.ctx.vlist:
                self.def_parser.log_error("Missing choices for enum {}".format(self.ctx.id))
            if not self.ctx.default:
                self.ctx.default = self.ctx.vlist[0].id
            self.ctx.metadata = Util.Container(
                count=self.ctx.cnt_id,
                vlist=self.ctx.vlist
                )

class DefinitionParser(Log.Debuggable):
    """
        Encapsulates logic to parse a definition file
    """

    def __init__(self, deftree, debug_mode=False):
        Log.Debuggable.__init__(self, debug_mode=debug_mode)

        self.deftree = deftree
        self.line_info = None
        self.def_root = os.path.dirname(deftree.get_filename())

        # Always has a context
        top_context = Context(def_parser=self)
        self.context_stack = [top_context]

        regex_flags = 0
        if Log.Logger.has_level(Log.LEVEL.EXTREME):
            regex_flags = re.DEBUG

        identifier_name = "[a-zA-Z0-9_]*"

        # line regexes, in order of matching
        with Log.CaptureStdout(self, "COMMENT_RE:"):
            self.comment_re = re.compile("[;#].*", regex_flags)
        with Log.CaptureStdout(self, "DIRECTIVE_RE:"):
            self.directive_re = re.compile(":.*", regex_flags)

        # directive regexes (preceding colon and whitespace stripped off), in order of matching
        with Log.CaptureStdout(self, "BLOCK_END_RE:"):
            self.block_end_re = re.compile("end$", regex_flags)
        with Log.CaptureStdout(self, "CONFIG_RE:"):
            self.config_re = re.compile(
                "config(_[bsif])?[ \t]+(" + identifier_name + ")$",
                regex_flags
                )
        with Log.CaptureStdout(self, "MENU_RE:"):
            self.menu_re = re.compile(
                "menu[ \t]+([a-zA-Z 0-9_-]{1,20})$",
                regex_flags
                )
        with Log.CaptureStdout(self, "INCLUDE_RE:"):
            self.include_re = re.compile("include[ ]+(.*)", regex_flags)

        # Block entry regexes, in order of matching
        with Log.CaptureStdout(self, "BLOCK_PARAM_RE::"):
            self.param_re = re.compile("(" + identifier_name + ")[ \t]+(.+)", regex_flags)

    def get_target(self):
        """Returns the target DefTree which is being parsed"""
        return self.deftree

    def log_error(self, err_text):
        """
            Log an error

            @note This does not return
        """
        Log.E("{}: {}".format(self.line_info, err_text), stackframe=3)

    def parse(self, line_info):
        """
            Parse a line from a package
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
            End parsing of the definition file
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
        if ctype == Context.CTYPE.CONFIG:
            self._config_end(cur_context)
        elif ctype == Context.CTYPE.MENU:
            self._menu_end(cur_context)
        else:
            assert ctype is not None

        self.context_stack.pop(-1)

    def _config_end(self, context):
        """
            End a config block

            Add the config to the def
        """
        scope_path = context.get_scope_path()
        self.debug("  {} @ {}".format(context.ctx.id, scope_path))
        scope = self.deftree.get_scope(scope_path)

        scope.add_param(DefTree.Parameter(
            pid=context.ctx.id,
            ptitle=context.ctx.title,
            ptype=context.ctx.ptype,
            pdesc=context.ctx.desc,
            pdefault=context.ctx.default,
            metadata=context.ctx.metadata
            ))

    def _config_start(self, quick_type, text):
        """
            Start a config block (for a single setting)

            Push a new context onto the stack with CTYPE.CONFIG.  Default settings for the block are
            set here.  For one-line "quick" settings, end the block immediately.
        """
        ptype = None
        if quick_type == "b":
            ptype = DefTree.PARAM_TYPE.BOOL
        elif quick_type == "s":
            ptype = DefTree.PARAM_TYPE.STRING
        elif quick_type == "i":
            ptype = DefTree.PARAM_TYPE.INT
        elif quick_type == "f":
            ptype = DefTree.PARAM_TYPE.FLOAT
        elif quick_type != "":
            self.log_error("Malformed quick-type suffix: {}".format(quick_type))

        cur_context = self.context_stack[-1]
        ctype = cur_context.get_ctype()
        if ctype not in [None, Context.CTYPE.MENU]:
            self.log_error("config is not allowed in this scope")

        new_context = Context(
            def_parser=self,
            prev_context=cur_context,
            line_info=self.line_info,
            ctx=Util.Container(
                ctype=Context.CTYPE.CONFIG,
                id=text,
                title=None,
                scope_path=None,
                desc=None,
                ptype=ptype,
                default=None,
                cnt_id=None,
                vlist=[],
                metadata=None
                )
            )
        self.context_stack.append(new_context)

        # End the block immediately if the quick version is used
        if quick_type != "":
            self._block_end()

    def _include_file(self, filename):
        """
            Include the contents of another file as if it was directly placed in this file
        """
        abs_filename = Util.get_abs_path(filename, self.def_root)

        # Save the definition root so that files paths can be relative to the included file
        old_def_root = self.def_root
        self.def_root = os.path.dirname(abs_filename)

        # Read the file using this object as the parser
        reader = LineReader.new(self, do_end=False)
        reader.read_file_by_name(abs_filename)

        # Restore the original definition root
        self.def_root = old_def_root

    def _menu_end(self, context):
        """
            End a menu block

            Add the def to the tree
        """
        if context.ctx.mdesc is not None:
            scope_path = context.get_scope_path()
            scope = self.deftree.get_scope(scope_path)
            scope.set_description(context.ctx.mdesc)

    def _menu_start(self, name):
        """
            Start a menu block (modifies the scope of contained menus and settings)

            Push a new context onto the stack with CTYPE.MENU.
        """
        cur_context = self.context_stack[-1]
        ctype = cur_context.get_ctype()
        if ctype not in [None, Context.CTYPE.MENU]:
            self.log_error("menu is not allowed in this scope")

        new_context = Context(
            def_parser=self,
            prev_context=cur_context,
            line_info=self.line_info,
            ctx=Util.Container(
                ctype=Context.CTYPE.MENU,
                mdesc=None
                )
            )
        # The name is a relative path
        new_context.scope_path = name
        self.debug("  {}".format(new_context.get_scope_path()))
        self.context_stack.append(new_context)

    def _parse_directive(self, text):
        """
            Parse directive text
        """
        m = Matcher.new(text)

        if m.is_fullmatch(self.config_re):
            qtype = ""
            if m[1] is not None:
                qtype = m[1][1]
            self.debug("CONFIG({}): {}".format(qtype, m[2]))
            self._config_start(qtype, m[2].lstrip())
        elif m.is_fullmatch(self.menu_re):
            self.debug("MENU: {}".format(m[1]))
            self._menu_start(m[1])
        elif m.is_fullmatch(self.block_end_re):
            self.debug("END")
            self._block_end()
        elif m.is_fullmatch(self.include_re):
            self.debug("INCLUDE")
            self._include_file(m[1])
        elif not m.found:
            self.log_error("Bad directive '{}'".format(text))

new = DefinitionParser

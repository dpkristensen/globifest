#/usr/bin/env python
"""
    globifest/ConfigParser.py - globifest

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
    Matcher

IDENTIFIER_NAME = "[a-zA-Z0-9_]+"

class ConfigParser(Log.Debuggable):
    """
        Encapsulates logic to parse a configuration file
    """

    def __init__(self, config, debug_mode=False):
        Log.Debuggable.__init__(self, debug_mode=debug_mode)

        self.config = config
        self.line_info = None
        self.comment_block = []

        regex_flags = 0
        if Log.Logger.has_level(Log.LEVEL.EXTREME):
            regex_flags = re.DEBUG

        # line regexes, in order of matching
        with Log.CaptureStdout(self, "COMMENT_RE:"):
            self.comment_re = re.compile("[;#][ \t]*(.*)", regex_flags)
        with Log.CaptureStdout(self, "SETTING_RE:"):
            self.setting_re = re.compile("(" + IDENTIFIER_NAME + ")[ \t]*=[ \t]*(.+)", regex_flags)

        # Regexes used in formatting of comments
        with Log.CaptureStdout(self, "BULLETED_LIST:"):
            self.bulleted_list_re = re.compile("[*\\-+#][ \t](.+)", regex_flags)

    def format_comments(self):
        """Format the comment block into something pretty"""
        ret = ""
        last = ""

        self.debug("COMMENT_BLOCK:")
        for s in self.comment_block:
            m_last = Matcher.new(last)

            if not ret:
                verb = "first"
                sep = "" # First line, no separator
            elif m_last.is_fullmatch(self.bulleted_list_re):
                verb = "list"
                sep = "\n" # new line in between list items
            elif (not last) != (not s):
                verb = "newline"
                sep = "\n" # New line in between paragraphs
            elif not last and not s:
                self.debug("  skip")
                continue # Skip contiguous sections of empty lines
            else:
                # Concatenate paragraph text
                verb = "concatenate"
                sep = " "
            self.debug("  {} '{}'".format(verb, s))
            last = s
            ret += sep + s

        return ret

    def get_target(self):
        """Returns the target Config which is being parsed"""
        return self.config

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

        m = Matcher.new(line)
        if (not line) or (line == ""):
            # empty, clear the comment block
            if self.comment_block:
                self.debug("COMMENT_CLEAR")
                self.comment_block.clear()
        elif m.is_fullmatch(self.comment_re):
            content = m[1].rstrip()
            # Concatenate contiguous comments into a list
            self.comment_block.append(content)
            self.debug("COMMENT += '{}'".format(content))
        elif m.is_fullmatch(self.setting_re):
            self.debug("ADD {} = {}".format(m[1], m[2]))
            self.config.add_value(line_info, m[1], m[2].rstrip())
            if self.comment_block:
                self.config.set_comment(line_info, m[1], self.format_comments())
                self.debug("COMMENT_CLEAR")
                self.comment_block.clear()
        else:
            self.log_error("Bad grammar: cannot parse {}".format(line_info))

    def parse_end(self):
        """
            End parsing of the config file
        """
        self.comment_block.clear()

        # Call get_settings() to finalize construction of the list
        self.config.get_settings()

new = ConfigParser

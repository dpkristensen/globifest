#/usr/bin/env python
"""
    globifest/globitest/testConfigParser.py - Tests for ConfigParser module

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

import copy
import io
import sys
import unittest

from GlobifestLib import Config, ConfigParser, LineReader, Log, Util

from Globitest import Helpers

class TestConfigParser(unittest.TestCase):

    def setUp(self):
        self.pipe = io.StringIO()
        Log.Logger.set_err_pipe(self.pipe)

    def doCleanups(self):
        Log.Logger.set_err_pipe(sys.stderr)
        if not self._outcome.success:
            if hasattr(self, "trace_msg"):
                print("TRACE:")
                print(self.trace_msg)
            if hasattr(self, "parser"):
                print("PARSER DEBUG LOG:")
                print(self.parser.get_debug_log())
            if hasattr(self, "pipe") and self.pipe:
                print("ERRORS:")
                print(self.pipe.getvalue().rstrip())
            if hasattr(self, "config"):
                print(self.config.get_settings())

        # Unreference the objects in reverse order
        if hasattr(self, "reader"):
            del self.reader
        if hasattr(self, "parser"):
            del self.parser
        if hasattr(self, "config"):
            del self.config
        if hasattr(self, "pipe"):
            del self.pipe

    def create_parser(self):
        self.config = Config.new()
        self.parser = ConfigParser.new(self.config, debug_mode=True)

        # The reader is not under test, but it provides a good way to feed strings to the parser
        self.reader = LineReader.new(self.parser)

    def parse_lines(self, *args):
        file = Helpers.new_file("\n".join(args))
        self.reader._read_file_obj(file)

    def verify_configs(self, expected):
        diff = expected.get_diff(self.config.get_settings().configs)
        if diff != Util.Container():
            print("UNMATCHED FIELDS:{}\n".format(diff))
            self.fail()

    def test_empty_config(self):
        self.create_parser()
        self.parse_lines(
            "; This is a comment",
            "# This is also a comment",
            "   ; This comment is indented"
            )

        self.verify_configs(Util.Container())

    def test_multiline_comments(self):
        self.create_parser()
        self.parse_lines(
            "; This comment is not part of the section below",
            "",
            "; To create a bulleted list,     ",
            "; this is what needs to be typed:",
            ";",
            ";\t* Item 1",
            "; * Item 2   ",
            ";  \t  ",
            "; Notice the blank line between the",
            ";     paragraph and the list.",
            "INT_VALUE=1",
            "; This comment is ignored"
            )

        self.verify_configs(Util.Container(
            INT_VALUE="1"
        ))

        expected_comment = "\n".join([
            "To create a bulleted list, this is what needs to be typed:",
            "",
            "* Item 1",
            "* Item 2",
            "",
            "Notice the blank line between the paragraph and the list."
            ])
        self.assertEqual(expected_comment, self.config.get_comment("INT_VALUE"))
        print(expected_comment)

    def test_multiple_values(self):
        self.create_parser()
        self.parse_lines(
            "INT_VALUE=123",
            "; Comment on ABC",
            "STR_VALUE=\"ABC\""
            )

        self.verify_configs(Util.Container(
            INT_VALUE="123",
            STR_VALUE="\"ABC\""
        ))

        self.assertEqual("", self.config.get_comment("INT_VALUE"))
        self.assertEqual("Comment on ABC", self.config.get_comment("STR_VALUE"))

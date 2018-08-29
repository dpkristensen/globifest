#/usr/bin/env python
"""
    globifest/globitest/testBuoondedStatefulParser.py - Tests for StatefulParser module

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

import io
import os
import sys
import unittest

from GlobifestLib import Log, BoundedStatefulParser
from GlobifestLib.StatefulParser import PARSE_STATUS, FLAGS

class TestBoundedStatefulParser(unittest.TestCase):

    def create_string_parser(self, text):
        self.parser = BoundedStatefulParser.new(text, "'", flags=FLAGS.DEBUG)
        return self.parser

    def create_dq_string_parser(self, text):
        self.parser = BoundedStatefulParser.new(text, "\"", flags=FLAGS.DEBUG)
        return self.parser

    def create_parenthases_parser(self, text):
        self.parser = BoundedStatefulParser.new(text, "(", ")", flags=FLAGS.DEBUG | FLAGS.MULTI_LEVEL)
        return self.parser

    def doCleanups(self):
        Log.Logger.set_err_pipe(sys.stderr)
        if not self._outcome.success:
            if hasattr(self, "parser"):
                print(self.parser.get_debug_log());
                self.parser = None
            if self.pipe:
                print(self.pipe.getvalue().rstrip())
            self.pipe = None

    def setUp(self):
        self.pipe = io.StringIO()
        Log.Logger.set_err_pipe(self.pipe)

    def test_begin_lbound1(self):
        p = self.create_parenthases_parser("")

        # Verify no error if stream has lbound at beginning
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("(foobaz"))
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.get_status())
        self.assertEqual("foobaz", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_begin_lbound2(self):
        p = self.create_parenthases_parser("")

        # Verify error if stream has lbound in middle
        self.assertEqual(PARSE_STATUS.ERROR, p.parse("foobaz("))
        self.assertEqual(PARSE_STATUS.ERROR, p.get_status())
        self.assertEqual("", p.get_parsed_text())
        self.assertEqual("foobaz(", p.get_remaining_text())

    def test_begin_rbound1(self):
        p = self.create_parenthases_parser("")

        # Verify error if stream has rbound at beginning
        self.assertEqual(PARSE_STATUS.ERROR, p.parse(")foobaz"))
        self.assertEqual(PARSE_STATUS.ERROR, p.get_status())
        self.assertEqual("", p.get_parsed_text())
        self.assertEqual(")foobaz", p.get_remaining_text())

    def test_begin_rbound2(self):
        p = self.create_parenthases_parser("")

        # Verify error if stream has rbound in middle
        self.assertEqual(PARSE_STATUS.ERROR, p.parse("foobaz)"))
        self.assertEqual(PARSE_STATUS.ERROR, p.get_status())
        self.assertEqual("", p.get_parsed_text())
        self.assertEqual("foobaz)", p.get_remaining_text())

    def test_begin_non_matching1(self):
        p = self.create_string_parser("")

        # Verify error if boundary is not present
        self.assertEqual(PARSE_STATUS.ERROR, p.parse("foobaz"))
        self.assertEqual(PARSE_STATUS.ERROR, p.get_status())
        self.assertEqual("", p.get_parsed_text())
        self.assertEqual("foobaz", p.get_remaining_text())

    def test_parenthases_complete1(self):
        # Verify section is found in initial load
        p = self.create_parenthases_parser("(hi)")
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_complete2(self):
        p = self.create_parenthases_parser("")

        # Verify section is found on first parse
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("(there)"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("there", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_complete3(self):
        p = self.create_parenthases_parser("")

        # Verify section is found on subsequent parse
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse(""))
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("(there)"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("there", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_complete4(self):
        p = self.create_parenthases_parser("")

        # Verify section is found split across parses with no intermediate text
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("(hi "))
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("there)"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi there", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_complete5(self):
        p = self.create_parenthases_parser("")

        # Verify section is found split across parses with intermediate text
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("(hi "))
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("there"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse(" guys)"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi there guys", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_create(self):
        p = self.create_parenthases_parser("")
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.get_status())
        self.assertEqual("", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse(""))
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.get_status())
        self.assertEqual("", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_nested_text(self):
        p = self.create_parenthases_parser("")

        # Verify nested parenthases are parsed correctly
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("((hi) there) guys"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("(hi) there", p.get_parsed_text())
        self.assertEqual(" guys", p.get_remaining_text())

    def test_parenthases_remaining_text1(self):
        p = self.create_parenthases_parser("")

        # Verify text after section is still present on single parse
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("(hi) there"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi", p.get_parsed_text())
        self.assertEqual(" there", p.get_remaining_text())

    def test_parenthases_remaining_text2(self):
        p = self.create_parenthases_parser("")

        # Verify text after section is still present on subsequent parse
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("(h"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("i) there"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi", p.get_parsed_text())
        self.assertEqual(" there", p.get_remaining_text())

    def test_parenthases_with_string1(self):
        # Verify parentheses with an embedded string
        p = self.create_parenthases_parser("('hi' there)")
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("'hi' there", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_with_string2(self):
        # Verify parentheses with an embedded string, using alternate string character
        p = self.create_parenthases_parser('("hi" there)')
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual('"hi" there', p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_with_string3(self):
        # Verify parentheses with an embedded string, with nesting levels before and after string
        p = self.create_parenthases_parser("((hi) 'there' (guys))")
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("(hi) 'there' (guys)", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_with_string4(self):
        # Verify parentheses with an embedded string, with unmatched parentheses inside the string
        p = self.create_parenthases_parser("('th(ere')")
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("'th(ere'", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_with_string5(self):
        # Verify parentheses with an embedded string, with unmatched parentheses inside the string
        p = self.create_parenthases_parser("('the)re')")
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("'the)re'", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_with_string6(self):
        # Verify a string with parentheses after the match
        p = self.create_parenthases_parser("(hi)'(there)'")
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi", p.get_parsed_text())
        self.assertEqual("'(there)'", p.get_remaining_text())

    def test_parenthases_with_string7(self):
        # Verify a string with parentheses and escapes
        p = self.create_parenthases_parser("(hi'(\\'there)')")
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi'(\\'there)'", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_with_string8(self):
        # Verify a string with parentheses and escapes
        p = self.create_parenthases_parser("")
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("(hi '"))
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("\\')there(\\'"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("' guys)"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi '\\')there(\\'' guys", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_parenthases_with_string9(self):
        # Verify a string with parentheses and mixed string delimeters
        p = self.create_parenthases_parser("(hi 'there\\'\") guys')")
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi 'there\\'\") guys'", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_alternate_bound(self):
        p = self.create_dq_string_parser("")

        # Verify string with different boundary characters
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("\"hi there'\""))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi there'", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_complete1(self):
        # Verify string is found in initial load
        p = self.create_string_parser("'hi'")
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_complete2(self):
        p = self.create_string_parser("")

        # Verify string is found on first parse
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("'there'"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("there", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_complete3(self):
        p = self.create_string_parser("")

        # Verify string is found on subsequent parse
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse(""))
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("'there'"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("there", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_complete4(self):
        p = self.create_string_parser("")

        # Verify string is found split across parses with no intermediate text
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("'hi "))
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("there'"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi there", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_complete5(self):
        p = self.create_string_parser("")

        # Verify string is found split across parses with intermediate text
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("'hi "))
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("there"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse(" guys'"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi there guys", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_create(self):
        p = self.create_string_parser("")
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.get_status())
        self.assertEqual("", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse(""))
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.get_status())
        self.assertEqual("", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_remaining_text1(self):
        p = self.create_string_parser("")

        # Verify text after string is still present on single parse
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("'hi' there"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi", p.get_parsed_text())
        self.assertEqual(" there", p.get_remaining_text())

    def test_string_remaining_text2(self):
        p = self.create_string_parser("")

        # Verify text after string is still present on subsequent parse
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("'hi"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("' there"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi", p.get_parsed_text())
        self.assertEqual(" there", p.get_remaining_text())

    def test_string_with_escape1(self):
        p = self.create_string_parser("'hi \\'there\\''")

        # Verify string parsing with escaped string delimiters
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi \\'there\\'", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_with_escape2(self):
        p = self.create_string_parser("'hi \\\"there\\\"'")

        # Verify string parsing with escaped string delimiter which is not the boundary
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi \\\"there\\\"", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_with_escape3(self):
        p = self.create_string_parser("")

        # Verify string parsing in sequence
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse("'hi"))
        self.assertEqual(PARSE_STATUS.INCOMPLETE, p.parse(" there "))
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("\\'guys'"))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi there \\'guys", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

    def test_string_with_escape4(self):
        p = self.create_dq_string_parser("")

        # Verify string with different boundary characters and escapes
        self.assertEqual(PARSE_STATUS.FINISHED, p.parse("\"hi \\\"guys\""))
        self.assertEqual(PARSE_STATUS.FINISHED, p.get_status())
        self.assertEqual("hi \\\"guys", p.get_parsed_text())
        self.assertEqual("", p.get_remaining_text())

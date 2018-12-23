#/usr/bin/env python
"""
    globifest/globitest/testLineReader.py - Tests for LineReader module

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
import unittest

from GlobifestLib import LineReader
from Globitest import Helpers

class TestLineReader(unittest.TestCase):

    def setUp(self):
        self.parser = Helpers.new_parser()
        self.reader = LineReader.new(self.parser)

    def test_embedded_bin_chars(self):
        """
            Test a file with embedded binary characters which could
            potentially break text processing:

            0x00 = Null (mostly universal)
            0x03 = ASCII End of text
            0x04 = ASCII End of transmission
            0x0C = ASCII Form feed)
            0x17 = ASCII End of transmission block
            0x1A = DOS End of File
            0x1C = ASCII File separator
        """
        file = io.StringIO("line\x00\x03\x04\x0c\x17\x1a\x1c1")
        self.reader._read_file_obj(file)

        self.assertEqual(len(self.parser.lines), 1);
        self.assertEqual(self.parser.lines[0].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[0].get_line(), 1)
        self.assertEqual(self.parser.lines[0].get_text(), "line\x00\x03\x04\x0c\x17\x1a\x1c1")

    def test_empty_file(self):
        file = Helpers.new_file("")
        self.reader._read_file_obj(file)

        self.assertEqual(len(self.parser.lines), 0)

    def test_multiline_file(self):
        file = Helpers.new_file(
            "\t this",
            "  is  ",
            "SPARTA!  "
            )
        self.reader._read_file_obj(file)

        self.assertEqual(len(self.parser.lines), 3)

        self.assertEqual(self.parser.lines[0].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[0].get_line(), 1)
        self.assertEqual(self.parser.lines[0].get_text(), "this")

        self.assertEqual(self.parser.lines[1].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[1].get_line(), 2)
        self.assertEqual(self.parser.lines[1].get_text(), "is")

        self.assertEqual(self.parser.lines[2].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[2].get_line(), 3)
        self.assertEqual(self.parser.lines[2].get_text(), "SPARTA!")

    def test_newline_mixed(self):
        file = io.StringIO("line1\r\nline2\nline3")
        self.reader._read_file_obj(file)

        self.assertEqual(len(self.parser.lines), 3, msg="{}".format([line_info.get_text() for line_info in self.parser.lines]))

        self.assertEqual(self.parser.lines[0].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[0].get_line(), 1)
        self.assertEqual(self.parser.lines[0].get_text(), "line1")

        self.assertEqual(self.parser.lines[1].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[1].get_line(), 2)
        self.assertEqual(self.parser.lines[1].get_text(), "line2")

        self.assertEqual(self.parser.lines[2].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[2].get_line(), 3)
        self.assertEqual(self.parser.lines[2].get_text(), "line3")

        # MAC OS-style newlines are not supported outside of the MAC OS
        # interpreter, and implementing support would slow down processing
        # on other platforms; so it is a non-requirement.
        #
        # Implementing a test for splitting on \r as well would break the test
        # on other platforms.

    def test_newline_unix(self):
        file = io.StringIO("line1\nline2")
        self.reader._read_file_obj(file)

        self.assertEqual(len(self.parser.lines), 2, msg="{}".format([line_info.get_text() for line_info in self.parser.lines]))

        self.assertEqual(self.parser.lines[0].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[0].get_line(), 1)
        self.assertEqual(self.parser.lines[0].get_text(), "line1")

        self.assertEqual(self.parser.lines[1].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[1].get_line(), 2)
        self.assertEqual(self.parser.lines[1].get_text(), "line2")

    def test_newline_windows(self):
        file = io.StringIO("line1\r\nline2")
        self.reader._read_file_obj(file)

        self.assertEqual(len(self.parser.lines), 2, msg="{}".format([line_info.get_text() for line_info in self.parser.lines]))

        self.assertEqual(self.parser.lines[0].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[0].get_line(), 1)
        self.assertEqual(self.parser.lines[0].get_text(), "line1")

        self.assertEqual(self.parser.lines[1].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[1].get_line(), 2)
        self.assertEqual(self.parser.lines[1].get_text(), "line2")

    def test_no_trailing_newline(self):
        file = io.StringIO("line1\nline2")
        self.reader._read_file_obj(file)

        self.assertEqual(len(self.parser.lines), 2);
        self.assertEqual(self.parser.lines[0].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[0].get_line(), 1)
        self.assertEqual(self.parser.lines[0].get_text(), "line1")

        self.assertEqual(self.parser.lines[1].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[1].get_line(), 2)
        self.assertEqual(self.parser.lines[1].get_text(), "line2")

    def test_trailing_newline(self):
        file = io.StringIO("line1\nline2\n")
        self.reader._read_file_obj(file)

        self.assertEqual(len(self.parser.lines), 2);
        self.assertEqual(self.parser.lines[0].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[0].get_line(), 1)
        self.assertEqual(self.parser.lines[0].get_text(), "line1")

        self.assertEqual(self.parser.lines[1].get_filename(), Helpers.TEST_FNAME)
        self.assertEqual(self.parser.lines[1].get_line(), 2)
        self.assertEqual(self.parser.lines[1].get_text(), "line2")

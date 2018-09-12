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

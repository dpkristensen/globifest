#/usr/bin/env python
"""
    globifest/globitest/testMatcher.py - Tests for Matcher module

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
import unittest

from GlobifestLib import Matcher

class TestMatcher(unittest.TestCase):

    word1 = re.compile("([a-z]+)")
    word2 = re.compile("([a-z]+) ([a-z]+)")
    numbers = re.compile("([0-9]+)")
    absent = re.compile("(!)")
    all = re.compile("([a-z]+) ([a-z]+) ([0-9]+)")

    def test_match(self):
        m = Matcher.new("hello abc 123")

        # Test matching a single word
        self.assertTrue(m.is_match(self.word1))
        self.assertTrue(m.found)
        self.assertEqual(m[0], "hello")
        self.assertEqual(m[1], "hello")
        self.assertEqual(m.get_num_matches(), 1)

        # Test matching an expression which is not in the text
        self.assertFalse(m.is_match(self.absent))
        self.assertFalse(m.found)
        self.assertEqual(m.get_num_matches(), 0)

        # Test matching an expression with multiple matches
        self.assertTrue(m.is_match(self.word2))
        self.assertTrue(m.found)
        self.assertEqual(m[0], "hello abc")
        self.assertEqual(m[1], "hello")
        self.assertEqual(m[2], "abc")
        self.assertEqual(m.get_num_matches(), 2)

        # Test matching an expression which is in the text, but not at the beginning
        self.assertFalse(m.is_match(self.numbers))
        self.assertFalse(m.found)
        self.assertEqual(m.get_num_matches(), 0)

        # Test matching the whole expression
        self.assertTrue(m.is_match(self.all))
        self.assertTrue(m.found)
        self.assertEqual(m[0], "hello abc 123")
        self.assertEqual(m[1], "hello")
        self.assertEqual(m[2], "abc")
        self.assertEqual(m[3], "123")
        self.assertEqual(m.get_num_matches(), 3)

    def test_full_match(self):
        m = Matcher.new("hello abc 123")

        # Test matching a single word
        self.assertFalse(m.is_fullmatch(self.word1))
        self.assertFalse(m.found)
        self.assertEqual(m.get_num_matches(), 0)

        # Test matching an expression which is not in the text
        self.assertFalse(m.is_fullmatch(self.absent))
        self.assertFalse(m.found)
        self.assertEqual(m.get_num_matches(), 0)

        # Test matching an expression with multiple matches
        self.assertFalse(m.is_fullmatch(self.word2))
        self.assertFalse(m.found)
        self.assertEqual(m.get_num_matches(), 0)

        # Test matching an expression which is in the text, but not at the beginning
        self.assertFalse(m.is_fullmatch(self.numbers))
        self.assertFalse(m.found)
        self.assertEqual(m.get_num_matches(), 0)

        # Test matching the whole expression
        self.assertTrue(m.is_fullmatch(self.all))
        self.assertTrue(m.found)
        self.assertEqual(m[0], "hello abc 123")
        self.assertEqual(m[1], "hello")
        self.assertEqual(m[2], "abc")
        self.assertEqual(m[3], "123")
        self.assertEqual(m.get_num_matches(), 3)

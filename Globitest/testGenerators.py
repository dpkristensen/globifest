#/usr/bin/env python
"""
    globifest/globitest/testGenerators.py - Tests for Generators module

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

import unittest

from GlobifestLib import Generators

class TestGenerators(unittest.TestCase):

    def test_c(self):
        generator = Generators.factory(
            gen_format="C", # Case-insensitive
            filename="config.h",
            formatter="ignored"
        )
        self.assertIsNotNone(generator)
        self.assertEqual(generator.get_filename(), "config.h")
        self.assertEqual(generator.FORMAT_TYPE, "c")
        self.assertEqual(generator.get_formatter(), None)

    def test_java(self):
        generator = Generators.factory(
            gen_format="jAVa", # Case-insensitive
            filename="config.java",
            formatter="irrelevant"
        )
        self.assertIsNotNone(generator)
        self.assertEqual(generator.get_filename(), "config.java")
        self.assertEqual(generator.FORMAT_TYPE, "java")
        self.assertEqual(generator.get_formatter(), None)

    def test_custom(self):
        generator = Generators.factory(
            gen_format="CusToM", # Case-insensitive
            filename="config.bin",
            formatter="bin_formatter.py"
        )
        self.assertIsNotNone(generator)
        self.assertEqual(generator.get_filename(), "config.bin")
        self.assertEqual(generator.FORMAT_TYPE, "custom")
        self.assertEqual(generator.get_formatter(), "bin_formatter.py")

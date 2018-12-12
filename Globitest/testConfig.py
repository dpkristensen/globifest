#/usr/bin/env python
"""
    globifest/globitest/testConfig.py - Tests for Config module

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

from GlobifestLib import \
    Config, \
    LineInfo, \
    Settings, \
    Util

class TestConfig(unittest.TestCase):

    def test_simple_set(self):
        cfg = Config.new(err_fatal=True)
        line = LineInfo.new("simple_set", 1, "stub")

        cfg.add_value(line, "FOO_INT_1", "5")
        cfg.add_value(line, "FOO_INT_2", "42")
        cfg.add_value(line, "FOO_STR_A", "\"Text A\"")
        cfg.add_value(line, "FOO_STR_B", "\"\"")

        # Just make sure the settings exist and are evaluatable
        settings = cfg.get_settings()
        self.assertIsInstance(settings, Settings.Settings)
        self.assertTrue(settings.evaluate("FOO_INT_1 == 5"))
        self.assertFalse(settings.evaluate("FOO_INT_1 == 42"))
        self.assertEqual("42", settings.get_value("FOO_INT_2"))
        self.assertEqual("\"Text A\"", settings.get_value("FOO_STR_A"))
        self.assertTrue(settings.evaluate("FOO_STR_B == ''"))
        self.assertFalse(settings.evaluate("FOO_STR_B == 'Text A'"))

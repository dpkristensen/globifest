#/usr/bin/env python
"""
    globifest/globitest/testSettings.py - Tests for Settings module

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
import sys
import unittest

from GlobifestLib import Settings, Log, Util
from Globitest import Helpers

class TestSettings(unittest.TestCase):

    def setUp(self):
        self.pipe = io.StringIO()
        Log.Logger.set_err_pipe(self.pipe)

    def doCleanups(self):
        config = getattr(self, "config", None)

        Log.Logger.set_err_pipe(sys.stderr)
        if not self._outcome.success:
            if config:
                print("CONFIG DEBUG LOG:")
                print(self.config.get_debug_log());
            if self.pipe:
                print("ERRORS:")
                print(self.pipe.getvalue().rstrip())

        if config:
            del self.config
        del self.pipe

    def create_config_set(self, config = Util.Container()):
        self.config = self.new_settings(config)

    def new_settings(self, config):
        return Settings.new(
            configs = config,
            debug_mode = True
            )

    def test_bool(self):
        self.create_config_set()
        self.assertTrue(self.config.evaluate("TRUE"))
        self.assertTrue(self.config.evaluate("TRUE"))

        self.create_config_set(Util.Container(
            v = "TRUE"
            ))
        self.assertTrue(self.config.evaluate("v == TRUE"))
        self.assertTrue(self.config.evaluate("v && TRUE"))
        self.assertFalse(self.config.evaluate("!v"))

    def test_compare_ints(self):
        self.create_config_set(Util.Container(
            a = "1",
            b = "2",
            c = "10"
            ))

        self.assertTrue(self.config.evaluate("a==1"))
        self.assertFalse(self.config.evaluate("a!=1"))

        self.assertFalse(self.config.evaluate("a<0"))
        self.assertFalse(self.config.evaluate("a<1"))
        self.assertTrue(self.config.evaluate("a<2"))

        self.assertFalse(self.config.evaluate("a<=0"))
        self.assertTrue(self.config.evaluate("a<=1"))
        self.assertTrue(self.config.evaluate("a<=2"))

        self.assertFalse(self.config.evaluate("a>2"))
        self.assertFalse(self.config.evaluate("a>1"))
        self.assertTrue(self.config.evaluate("a>0"))

        self.assertFalse(self.config.evaluate("a>=2"))
        self.assertTrue(self.config.evaluate("a>=1"))
        self.assertTrue(self.config.evaluate("a>=0"))

        # Ensure the numeric comparison works with two identifiers
        self.assertTrue(self.config.evaluate("a < b"))

        # Ensure the comparison is numeric, not string
        self.assertTrue(self.config.evaluate("2 < 10"))
        self.assertTrue(self.config.evaluate("b < c"))

    def test_compare_logical_and(self):
        self.create_config_set()

        self.assertFalse(self.config.evaluate("FALSE && FALSE"))
        self.assertFalse(self.config.evaluate("TRUE && FALSE"))
        self.assertFalse(self.config.evaluate("FALSE && TRUE"))
        self.assertTrue(self.config.evaluate("TRUE && TRUE"))

    def test_compare_logical_or(self):
        self.create_config_set()

        self.assertFalse(self.config.evaluate("FALSE || FALSE"))
        self.assertTrue(self.config.evaluate("TRUE || FALSE"))
        self.assertTrue(self.config.evaluate("FALSE || TRUE"))
        self.assertTrue(self.config.evaluate("TRUE || TRUE"))

    def test_extend(self):
        self.create_config_set(Util.Container(
            a="12",
            b="34"
            ))
        self.config.extend(self.new_settings(Util.Container(
            b="56",
            c="78"
        )))

        self.assertTrue(self.config.evaluate("a==12"))
        self.assertTrue(self.config.evaluate("b==56"))
        self.assertTrue(self.config.evaluate("c==78"))

    def test_ident_not_found(self):
        self.create_config_set()
        try:
            self.assertFalse(self.config.evaluate("a==1"))
            self.fail() # Should never reach this
        except Log.GlobifestException as e:
            self.assertEqual(str(e), "a not defined")

    def test_int(self):
        self.create_config_set()
        self.assertTrue(self.config.evaluate("1"))

    def test_invert(self):
        self.create_config_set()

        self.assertTrue(self.config.evaluate("!FALSE"))
        self.assertFalse(self.config.evaluate("!TRUE"))

    def test_parens(self):
        self.create_config_set()

        self.assertTrue(self.config.evaluate("  FALSE || FALSE  ==  FALSE  || TRUE "))
        self.assertTrue(self.config.evaluate(" (FALSE || FALSE) ==  FALSE  || TRUE "))
        self.assertFalse(self.config.evaluate(" FALSE || FALSE  == (FALSE  || TRUE)"))
        self.assertFalse(self.config.evaluate("(FALSE || FALSE) == (FALSE  || TRUE)"))
        self.assertTrue(self.config.evaluate("  FALSE || (FALSE ==  FALSE) || TRUE "))

        self.assertTrue(self.config.evaluate("FALSE || (FALSE == FALSE) || FALSE"))

        self.assertTrue(self.config.evaluate("TRUE && ((FALSE == FALSE) || FALSE)"))
        self.assertFalse(self.config.evaluate("TRUE && ((FALSE == TRUE) || FALSE)"))

    def test_string(self):
        self.create_config_set(Util.Container(
            s = "\"hi\""
            ))

        self.assertTrue(self.config.evaluate("s == \"hi\""))
        self.assertFalse(self.config.evaluate("s != \"hi\""))
        self.assertFalse(self.config.evaluate("s == \"HI\""))

        for expression in [
            "s < \"hi\"",
            "s <= \"hi\"",
            "s > \"hi\"",
            "s >= \"hi\"",
            "s && \"hi\"",
            "s || \"hi\"",
            "s < s",
            ]:
            try:
                self.assertFalse(self.config.evaluate(expression))
                self.fail() # Should never reach this
            except Log.GlobifestException:
                pass

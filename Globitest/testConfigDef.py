#/usr/bin/env python
"""
    globifest/globitest/testConfigDef.py - Tests for ConfigDef module

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

from GlobifestLib import ConfigDef, Util

class TestConfigDef(unittest.TestCase):

    def setUp(self):
        self.pa = ConfigDef.Parameter(
            pid="IDENTIFIER_A",
            ptitle="Value A",
            ptype=ConfigDef.PARAM_TYPE.BOOL,
            pdesc="Description of A",
            pdefault="FALSE"
            )
        self.pb = ConfigDef.Parameter(
            pid="IDENTIFIER_B",
            ptitle="Value B",
            ptype=ConfigDef.PARAM_TYPE.STRING,
            # Empty description
            pdefault="Default Text"
            )
        self.pc = ConfigDef.Parameter(
            pid="IDENTIFIER_C",
            ptitle="Value C",
            ptype=ConfigDef.PARAM_TYPE.NUMERIC,
            pdesc="Description of C"
            # No default
            )

    def test_create_empty_set(self):
        c = ConfigDef.new()
        self.assertEqual(c.get_children(), Util.Container())
        self.assertEqual(c.get_name(), "/")
        self.assertEqual(c.get_params(), [])

    def test_create_params(self):
        self.assertEqual(self.pa.get_default_value(), "FALSE")
        self.assertEqual(self.pa.get_description(), "Description of A")
        self.assertEqual(self.pa.get_identifier(), "IDENTIFIER_A")
        self.assertEqual(self.pa.get_title(), "Value A")
        self.assertEqual(self.pa.get_type(), ConfigDef.PARAM_TYPE.BOOL)

        self.assertEqual(self.pb.get_default_value(), "Default Text")
        self.assertEqual(self.pb.get_description(), "")
        self.assertEqual(self.pb.get_identifier(), "IDENTIFIER_B")
        self.assertEqual(self.pb.get_title(), "Value B")
        self.assertEqual(self.pb.get_type(), ConfigDef.PARAM_TYPE.STRING)

        self.assertEqual(self.pc.get_default_value(), None)
        self.assertEqual(self.pc.get_description(), "Description of C")
        self.assertEqual(self.pc.get_identifier(), "IDENTIFIER_C")
        self.assertEqual(self.pc.get_title(), "Value C")
        self.assertEqual(self.pc.get_type(), ConfigDef.PARAM_TYPE.NUMERIC)

    def test_flat_config(self):
        c = ConfigDef.new()

        self.assertEqual(self.pa, c.add_param(self.pa))
        self.assertEqual(self.pb, c.add_param(self.pb))
        self.assertEqual(self.pc, c.add_param(self.pc))

        self.assertEqual(c.get_params(), [self.pa, self.pb, self.pc])

    def test_nested_config(self):
        c = ConfigDef.new()

        c.add_child_scope("scope_a").add_param(self.pa)
        c.add_child_scope("scope_b").add_param(self.pb)
        c.add_child_scope("scope_c").add_param(self.pc)
        scope_abc = c.add_child_scope("scope_abc")
        scope_abc.add_param(self.pa)
        scope_abc.add_param(self.pb)
        scope_abc.add_param(self.pc)

        self.assertEqual(c.get_params(), [])
        self.assertEqual(c.get_children().scope_a.get_name(), "scope_a")
        self.assertEqual(c.get_children().scope_a.get_params(), [self.pa])
        self.assertEqual(c.get_children().scope_b.get_name(), "scope_b")
        self.assertEqual(c.get_children().scope_b.get_params(), [self.pb])
        self.assertEqual(c.get_children().scope_c.get_name(), "scope_c")
        self.assertEqual(c.get_children().scope_c.get_params(), [self.pc])
        self.assertEqual(c.get_children().scope_abc.get_name(), "scope_abc")
        self.assertEqual(c.get_children().scope_abc.get_params(), [self.pa, self.pb, self.pc])

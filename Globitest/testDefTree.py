#/usr/bin/env python
"""
    globifest/globitest/testDefTree.py - Tests for DefTree module

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

from GlobifestLib import DefTree, Settings, Util

class TestDefTree(unittest.TestCase):

    def setUp(self):
        self.pa = DefTree.Parameter(
            pid="IDENTIFIER_A",
            ptitle="Value A",
            ptype=DefTree.PARAM_TYPE.BOOL,
            pdesc="Description of A",
            pdefault="FALSE"
            )
        self.pb = DefTree.Parameter(
            pid="IDENTIFIER_B",
            ptitle="Value B",
            ptype=DefTree.PARAM_TYPE.STRING,
            # Empty description
            pdefault="Default Text"
            )
        self.pc = DefTree.Parameter(
            pid="IDENTIFIER_C",
            ptitle="Value C",
            ptype=DefTree.PARAM_TYPE.INT,
            pdesc="Description of C"
            # No default
            )
        self.pd = DefTree.Parameter(
            pid="IDENTIFIER_D",
            ptitle="", # Empty title
            ptype=DefTree.PARAM_TYPE.FLOAT,
            pdesc="Description of D"
            # No default
            )

    def test_create_empty_set(self):
        c = DefTree.new()
        self.assertEqual(c.get_children(), Util.Container())
        self.assertEqual(c.get_filename(), "")
        self.assertEqual(c.get_name(), "/")
        self.assertEqual(c.get_params(), [])

    def test_create_params(self):
        self.assertEqual(self.pa.get_default_value(), "FALSE")
        self.assertEqual(self.pa.get_description(), "Description of A")
        self.assertEqual(self.pa.get_identifier(), "IDENTIFIER_A")
        self.assertEqual(self.pa.get_title(), "Value A")
        self.assertEqual(self.pa.get_type(), DefTree.PARAM_TYPE.BOOL)
        self.assertEqual(self.pa.get_text(), "Value A")
        self.assertEqual(str(self.pa), "id=IDENTIFIER_A type=BOOL title=Value A default=FALSE desc=Description of A")

        self.assertEqual(self.pb.get_default_value(), "Default Text")
        self.assertEqual(self.pb.get_description(), "")
        self.assertEqual(self.pb.get_identifier(), "IDENTIFIER_B")
        self.assertEqual(self.pb.get_title(), "Value B")
        self.assertEqual(self.pb.get_type(), DefTree.PARAM_TYPE.STRING)
        self.assertEqual(self.pb.get_text(), "Value B")
        self.assertEqual(str(self.pb), "id=IDENTIFIER_B type=STRING title=Value B default=Default Text")

        self.assertEqual(self.pc.get_default_value(), None)
        self.assertEqual(self.pc.get_description(), "Description of C")
        self.assertEqual(self.pc.get_identifier(), "IDENTIFIER_C")
        self.assertEqual(self.pc.get_title(), "Value C")
        self.assertEqual(self.pc.get_type(), DefTree.PARAM_TYPE.INT)
        self.assertEqual(self.pc.get_text(), "Value C")
        self.assertEqual(str(self.pc), "id=IDENTIFIER_C type=INT title=Value C desc=Description of C")

        self.assertEqual(self.pd.get_default_value(), None)
        self.assertEqual(self.pd.get_description(), "Description of D")
        self.assertEqual(self.pd.get_identifier(), "IDENTIFIER_D")
        self.assertEqual(self.pd.get_title(), "")
        self.assertEqual(self.pd.get_type(), DefTree.PARAM_TYPE.FLOAT)
        self.assertEqual(self.pd.get_text(), "IDENTIFIER_D")
        self.assertEqual(str(self.pd), "id=IDENTIFIER_D type=FLOAT desc=Description of D")

    def test_flat_config(self):
        c = DefTree.new(filename="test.def")

        self.assertEqual(self.pa, c.add_param(self.pa))
        self.assertEqual(self.pb, c.add_param(self.pb))
        self.assertEqual(self.pc, c.add_param(self.pc))

        self.assertEqual(c.get_name(), "/")
        self.assertEqual(c.get_filename(), "test.def")
        self.assertEqual(c.get_params(), [self.pa, self.pb, self.pc])

        search_scope = c.get_scope("/")
        self.assertEqual(search_scope.get_name(), "/")
        self.assertEqual(search_scope.get_params(), [self.pa, self.pb, self.pc])

        search_scope = c.get_scope("")
        self.assertEqual(search_scope.get_name(), "/")
        self.assertEqual(search_scope.get_params(), [self.pa, self.pb, self.pc])

    def test_nested_config(self):
        c = DefTree.new()

        c.add_child_scope("scope_a").add_param(self.pa)
        c.add_child_scope("scope_b").add_param(self.pb)
        c.set_description("top")
        scope_c = c.add_child_scope("scope_c")
        scope_c.add_param(self.pc)
        scope_abc = scope_c.add_child_scope("scope_abc")
        scope_abc.add_param(self.pa)
        scope_abc.add_param(self.pb)
        scope_abc.add_param(self.pc)
        scope_abc.set_description("123")

        self.assertEqual(c.get_description(), "top")
        self.assertEqual(c.get_params(), [])
        self.assertEqual(c.get_children().scope_a.get_description(), "")
        self.assertEqual(c.get_children().scope_a.get_name(), "scope_a")
        self.assertEqual(c.get_children().scope_a.get_params(), [self.pa])
        self.assertEqual(c.get_children().scope_b.get_name(), "scope_b")
        self.assertEqual(c.get_children().scope_b.get_params(), [self.pb])
        self.assertEqual(c.get_children().scope_c.get_name(), "scope_c")
        self.assertEqual(c.get_children().scope_c.get_params(), [self.pc])
        self.assertEqual(
            c.get_children().scope_c.get_children().scope_abc.get_description(),
            "123"
            )
        self.assertEqual(
            c.get_children().scope_c.get_children().scope_abc.get_name(),
            "scope_abc"
            )
        self.assertEqual(
            c.get_children().scope_c.get_children().scope_abc.get_params(),
            [self.pa, self.pb, self.pc]
            )

        search_scope = c.get_scope("/scope_a")
        self.assertEqual(search_scope.get_name(), "scope_a")
        self.assertEqual(search_scope.get_params(), [self.pa])

        search_scope = c.get_scope("scope_b/")
        self.assertEqual(search_scope.get_name(), "scope_b")
        self.assertEqual(search_scope.get_params(), [self.pb])
        search_scope = c.get_scope("scope_b")
        self.assertEqual(search_scope.get_name(), "scope_b")

        search_scope = c.get_scope("/scope_c")
        self.assertEqual(search_scope.get_name(), "scope_c")
        self.assertEqual(search_scope.get_params(), [self.pc])

        search_scope = c.get_scope("/scope_c/scope_abc")
        self.assertEqual(search_scope.get_description(), "123")
        self.assertEqual(search_scope.get_name(), "scope_abc")
        self.assertEqual(search_scope.get_params(), [self.pa, self.pb, self.pc])

        c.get_children().scope_c.get_children().scope_abc.set_description("456")
        self.assertEqual(search_scope.get_description(), "123\n\n456")
        search_scope.set_description("789")
        self.assertEqual(search_scope.get_description(), "123\n\n456\n\n789")

    def test_get_relevant_params(self):
        c = DefTree.new(filename="test.def")

        self.assertEqual(self.pa, c.add_param(self.pa))
        self.assertEqual(self.pb, c.add_param(self.pb))
        self.assertEqual(self.pc, c.add_param(self.pc))


        settings = Settings.new(configs=Util.Container(
            # Values in the list are interspersed with values that are not in the list
            IDENTIFIER_A="A",
            IDENTIFIER_X="X",
            IDENTIFIER_B="B",
            IDENTIFIER_Y="Y",
            IDENTIFIER_Z="Z",
            IDENTIFIER_C="C"
        ))
        self.assertEqual(c.get_relevant_params(settings), [
                Util.Container(param=self.pa, value="A"),
                Util.Container(param=self.pb, value="B"),
                Util.Container(param=self.pc, value="C")
            ])

    def test_validate_type(self):
        test_tbl = [
            ("BOOL", DefTree.PARAM_TYPE.BOOL),
            ("bool", DefTree.PARAM_TYPE.BOOL),
            ("BoOl", DefTree.PARAM_TYPE.BOOL),

            ("STRING", DefTree.PARAM_TYPE.STRING),
            ("string", DefTree.PARAM_TYPE.STRING),
            ("StrIng", DefTree.PARAM_TYPE.STRING),

            ("INT", DefTree.PARAM_TYPE.INT),
            ("int", DefTree.PARAM_TYPE.INT),
            ("iNt", DefTree.PARAM_TYPE.INT),

            ("FLOAT", DefTree.PARAM_TYPE.FLOAT),
            ("float", DefTree.PARAM_TYPE.FLOAT),
            ("flOAt", DefTree.PARAM_TYPE.FLOAT),

            ("Bol",     None),
            ("nt",      None),
            ("str1ng",  None),
            ("fl0at",   None),
            (None,      None)
            ]

        for t in test_tbl:
            self.assertEqual(
                DefTree.validate_type(t[0]),
                t[1],
                msg="{} -> {}".format(t[0], t[1])
                )

    def test_validate_value_bool(self):
        test_tbl = [
            ("TRUE", True),
            ("true", True),
            ("trUe", True),

            ("FALSE", False),
            ("false", False),
            ("False", False),

            ("fa1se",   None),
            ("treu",    None),
            ("no",      None),
            ("nil",     None),
            (None,      None)
            ]

        for t in test_tbl:
            self.assertEqual(
                DefTree.validate_value(DefTree.PARAM_TYPE.BOOL, t[0]),
                t[1],
                msg="'{}' -> {}".format(t[0], t[1])
                )

    def test_validate_value_float(self):
        test_tbl = [
            (   "0",       0.0),
            ( "0.0",       0.0),
            ("-100",    -100.0),
            ("-100.5",  -100.5),
            ( "200.1",   200.1),
            ("+300",     300.0),
            ("+300.002", 300.002),

            ("abc", None),
            ("O",   None),
            (None,  None)
            ]

        for t in test_tbl:
            self.assertEqual(
                DefTree.validate_value(DefTree.PARAM_TYPE.FLOAT, t[0]),
                t[1],
                msg="'{}' -> {}".format(t[0], t[1])
                )

    def test_validate_value_int(self):
        test_tbl = [
            (   "0",    0),
            ( " 0 ",    0),
            ("-100", -100),
            ( "200",  200),
            ("+300",  300),

            ("1.5", None),
            ("abc", None),
            ("O",   None),
            (None,  None)
            ]

        for t in test_tbl:
            self.assertEqual(
                DefTree.validate_value(DefTree.PARAM_TYPE.INT, t[0]),
                t[1],
                msg="'{}' -> {}".format(t[0], t[1])
                )

    def test_validate_value_string(self):
        test_tbl = [
            ("", ""),
            ("lel", "lel"),
            ("\"", '"'),
            (None, None)
            ]

        for t in test_tbl:
            self.assertEqual(
                DefTree.validate_value(DefTree.PARAM_TYPE.STRING, t[0]),
                t[1],
                msg="'{}' -> {}".format(t[0], t[1])
                )

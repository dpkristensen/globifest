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

from GlobifestLib import ConfigDef, ConfigParser, LineReader, Log, Util

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
            if hasattr(self, "configdef"):
                print("PARSED CONFIGS:")
                self.configdef.walk(ConfigDef.PrintObserver())
            else:
                print("NO CONFIGS!")
            if hasattr(self, "cur_scope"):
                print("In scope: {}".format("/".join(self.cur_scope)))

        # Unreference the objects in reverse order
        if hasattr(self, "cur_scope"):
            del self.cur_scope
        if hasattr(self, "reader"):
            del self.reader
        if hasattr(self, "parser"):
            del self.parser
        if hasattr(self, "configdef"):
            del self.configdef
        if hasattr(self, "pipe"):
            del self.pipe

    def create_parser(self):
        # The ConfigDef and reader are not under test, but simple enough to use directly
        self.configdef = ConfigDef.new()
        self.parser = ConfigParser.new(self.configdef, debug_mode=True)

        # The reader is not under test, but it provides a good way to feed strings to the parser
        self.reader = LineReader.new(self.parser)

    def parse_lines(self, *args):
        file = Helpers.new_file("\n".join(args))
        self.reader._read_file_obj(file)

    def verify_configdef(self, expected):
        self.cur_scope = []
        self.assertEqual(self.configdef.get_name(), "/")
        self.assertListEqual(list(expected.keys()), ["/"])
        self._verify_scope(self.configdef, expected.get("/"), "/")
        del self.cur_scope

    def verify_params(self, expected):
        actual = list(str(p) for p in self.configdef.get_params())
        self.assertListEqual(expected, actual)

    def _verify_scope(self, scope, expected, name=None):
        # verify the name
        self.cur_scope.append(name or scope.get_name())

        # Verify the description
        expected_desc = expected.get("description", "")
        self.assertEqual(expected_desc, scope.get_description())

        # Verify the parameters
        expected_params = expected.get("params", [])
        params = list(str(p) for p in scope.get_params())
        self.assertListEqual(expected_params, params)

        # Copy the list of expected children, so we can modify it as we traverse
        no_children = Util.Container()
        expected_children = copy.copy(expected.get("children", no_children))
        # Match up actual children with expected children
        for actual_child in scope.get_children():
            expected_child = expected_children.get(actual_child[0], None)
            if expected_child is None:
                self.fail("Unexpected child {}".format(actual_child))
            else:
                # Matched a child by identifier, verify the sub-scope
                self._verify_scope(actual_child[1], expected_child)
                expected_children.pop(actual_child[0])
        if expected_children:
            # Print out the missing children
            self.fail("Missing children: {}".format(",".join(expected_children.keys())))

        self.cur_scope.pop()

    def test_full(self):
        self.create_parser()
        self.parse_lines(
            ":config FOO_SUPPORT",
            "    type BOOL",
            "    title \"Enable\"",
            "    default TRUE",
            "    description \"The FOO module doesn't do much\"",
            ":end",
            ":config FOO_CONFIG_PATH",
            "    type STRING",
            "    title \"Config Path\"",
            "    default \"foo/foo.cfg\"",
            "    description \"Path to \"FOO\" configuration file\"",
            ":end",
            ":config FOO_MAX_BAZ",
            "    type INT",
            "    title \"Max Baz\"",
            "    default 10",
            "    description \"Max number of BAZ supported\"",
            ":end",
            ":config FOO_PRECISION",
            "    type FLOAT",
            "    title \"Precision\"",
            "    default 0.5",
            "    description \"Precision to use\"",
            ":end",
            )

        self.verify_configdef(Util.Container(**{
            "/" : Util.Container(
                params = [
                "id=FOO_SUPPORT type=BOOL title=\"Enable\" default=True desc=\"The FOO module doesn't do much\"",
                "id=FOO_CONFIG_PATH type=STRING title=\"Config Path\" default=\"foo/foo.cfg\" desc=\"Path to \"FOO\" configuration file\"",
                "id=FOO_MAX_BAZ type=INT title=\"Max Baz\" default=10 desc=\"Max number of BAZ supported\"",
                "id=FOO_PRECISION type=FLOAT title=\"Precision\" default=0.5 desc=\"Precision to use\""
                ])
            }))

    def test_menu_block(self):
        self.create_parser()
        self.parse_lines(
            ":menu M1",
            "    description Menu 1",
            "    :config_b M1_1",
            "    :config TOP_1",
            "        type INT",
            "        menu /", # Absolute path overrides menu
            "    :end",
            ":end",
            ":menu M2",
            "    :config_b M2_1",
            "    :config M2_A_1",
            "        type BOOL",
            "        menu A", # Relative path appends to path
            "    :end",
            "    description Menu 2", # Does not have to be before configs
            "    :menu B", # Nested menu context
            "        description Menu 2-B",
            "        :config_b M2_B_1",
            "    :end",
            "    :config M2_B_C_1",
            "        type BOOL",
            "        menu B/C", # Relative path to existing menu
            "    :end",
            "    :menu B", # Add more stuff to B
            "        description    Moar stuff for B", # Append
            "        :config_i M2_B_2",
            "    :end",
            "    :config M1_2",
            "        type INT",
            "        menu /M1", # Absolute path to different scope
            "    :end",
            ":end"
            )

        self.verify_configdef(Util.Container(**{
            "/" : Util.Container(
                children = Util.Container(**{
                    "M1" : Util.Container(
                        description = "Menu 1",
                        params = [
                            "id=M1_1 type=BOOL",
                            "id=M1_2 type=INT"
                            ]
                        ),
                    "M2" : Util.Container(
                        description = "Menu 2",
                        params = [ "id=M2_1 type=BOOL" ],
                        children = Util.Container(**{
                            "A" : Util.Container(
                                params = [ "id=M2_A_1 type=BOOL" ]
                                ),
                            "B" : Util.Container(
                                description = "Menu 2-B\n\nMoar stuff for B",
                                params = [
                                    "id=M2_B_1 type=BOOL",
                                    "id=M2_B_2 type=INT"
                                    ],
                                children = Util.Container(**{
                                    "C" : Util.Container(
                                        params = [ "id=M2_B_C_1 type=BOOL" ]
                                        )
                                    })
                                )
                            })
                        )
                    }),
                params = [ "id=TOP_1 type=INT" ]
                )
            }))

    def test_menu_param(self):
        self.create_parser()
        self.parse_lines(
            ":config_b TOP_1",
            ":config TOP_2",
            "    type INT",
            "    menu /", # Absolute path (root)
            ":end",
            ":config MENU_A",
            "    type BOOL",
            "    menu /A", # Absolute path
            ":end",
            ":config MENU_ABC",
            "    type BOOL",
            "    menu ABC", # Relative path
            ":end",
            ":config MENU_ABC_DEF",
            "    type BOOL",
            "    menu /ABC/def", # Absolute path
            ":end",
            ":config_b TOP_3"
            )

        self.verify_configdef(Util.Container(**{
            "/" : Util.Container(
                children = Util.Container(**{
                    "A" : Util.Container(
                        params = [ "id=MENU_A type=BOOL" ]
                        ),
                    "ABC" : Util.Container(
                        params = [ "id=MENU_ABC type=BOOL" ],
                        children = Util.Container(**{
                            "def" : Util.Container(
                                params = [ "id=MENU_ABC_DEF type=BOOL" ]
                                )
                            })
                        )
                    }),
                params = [
                    "id=TOP_1 type=BOOL",
                    "id=TOP_2 type=INT",
                    "id=TOP_3 type=BOOL"
                    ]
                )
            }))

    def test_minimal(self):
        self.create_parser()
        self.parse_lines(
            ":config MY_DEFAULT_CONFIG1",
            "    type BOOL",
            ":end",
            ":config MY_DEFAULT_CONFIG2",
            "    type STRING",
            ":end",
            ":config MY_DEFAULT_CONFIG3",
            "    type INT",
            ":end",
            ":config MY_DEFAULT_CONFIG4",
            "    type FLOAT",
            ":end"
            )

        self.verify_configdef(Util.Container(**{
            "/" : Util.Container(
                params = [
                "id=MY_DEFAULT_CONFIG1 type=BOOL",
                "id=MY_DEFAULT_CONFIG2 type=STRING",
                "id=MY_DEFAULT_CONFIG3 type=INT",
                "id=MY_DEFAULT_CONFIG4 type=FLOAT"
                ])
            }))

    def test_quick_values(self):
        self.create_parser()
        self.parse_lines(
            ":config_b MY_BOOL_CONFIG",
            ":config_s MY_STRING_CONFIG",
            ":config_i MY_INT_CONFIG",
            ":config_f MY_FLOAT_CONFIG"
            )

        self.verify_configdef(Util.Container(**{
            "/" : Util.Container(
                params = [
                "id=MY_BOOL_CONFIG type=BOOL",
                "id=MY_STRING_CONFIG type=STRING",
                "id=MY_INT_CONFIG type=INT",
                "id=MY_FLOAT_CONFIG type=FLOAT"
                ])
            }))

#/usr/bin/env python
"""
    globifest/globitest/testProjectParser.py - Tests for ProjectParser module

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

from GlobifestLib import Project, ProjectParser, LineReader, Log, Util

from Globitest import Helpers

class TestProjectParser(unittest.TestCase):

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
            if hasattr(self, "project"):
                print("PROJECT:")
                print("  name={}".format(self.project.get_name()))
                for layer in self.project.get_layer_names():
                    print("  Layer({})".format(layer))
                    for variant in self.project.get_variant_names(layer):
                        print("    {}".format(variant))
                for pkg in self.project.get_packages():
                    print("  pkg {}".format(pkg))

        # Unreference the objects in reverse order
        if hasattr(self, "reader"):
            del self.reader
        if hasattr(self, "parser"):
            del self.parser
        if hasattr(self, "pipe"):
            del self.pipe

    def create_parser(self):
        self.project = Project.new()
        self.parser = ProjectParser.new(self.project, debug_mode=True)

        # The reader is not under test, but it provides a good way to feed strings to the parser
        self.reader = LineReader.new(self.parser)

    def parse_lines(self, *args):
        file = Helpers.new_file("\n".join(args))
        self.reader._read_file_obj(file)

    def verify_project(self, expected):
        prj = self.parser.get_target();

        # Verify simple properties
        self.assertIsNotNone(prj)
        self.assertEqual(prj.get_name(), expected.name)

        # Verify layers
        for actual_layer_name, expected_layer in zip(prj.get_layer_names(), expected.layers):
            self.assertEqual(actual_layer_name, expected_layer.name)
            for actual_variant_name, expected_variant in zip(prj.get_variant_names(actual_layer_name), expected_layer.variants):
                self.assertEqual(actual_variant_name, expected_variant.name)
                self.assertEqual(
                    prj.get_target(actual_layer_name, actual_variant_name).filename,
                    expected_variant.filename
                    )

        # Verify packages
        self.assertEqual(prj.get_packages(), expected.packages)

        # Verify dependencies
        actual_dependencies = Util.Container()
        for dep_name, dependency in prj.get_dependencies():
            actual_action_list = []
            for action in dependency.get_actions():
                actual_action_list.append(Util.Container(
                    id=action.ACTION_TYPE,
                    arg=action.arg
                    ))
            actual_dependencies[dep_name] = actual_action_list
        self.assertEqual(Util.Container(), actual_dependencies.get_diff(expected.dependencies))

    def test_dependencies(self):
        self.create_parser()
        self.parse_lines(
            ":project DepTest",
            "    :dependency FOO",
            "        dest chu.zip",
            "        url https://foohub.com/foo_man/FOO/master/chu.zip",
            "        extract chu/",
            "    :end",
            "    :ext_package FOO extract/chu.gman",
            "    :dependency BAR",
            "        dest bar.bin",
            "        url https://foohub.com/foo_man/FOO/master/bar.bin",
            "    :end",
            "    :lcl_package BAR external/BAR.gman",
            ":end",
            )

        self.verify_project(Util.Container(**{
            "name" : "DepTest",
            "layers" : [],
            "packages" : [
                Util.Container(
                    filename="extract/chu.gman",
                    file_root=Project.ROOT.DEPENDENCY,
                    module_root=Project.ROOT.SOURCE,
                    module_id="FOO"
                    ),
                Util.Container(
                    filename="external/BAR.gman",
                    file_root=Project.ROOT.SOURCE,
                    module_root=Project.ROOT.DEPENDENCY,
                    module_id="BAR"
                    )
                ],
            "dependencies" : Util.Container(**{
                "FOO" : [
                    Util.Container(
                        id="dest",
                        arg="chu.zip"
                        ),
                    Util.Container(
                        id="url",
                        arg="https://foohub.com/foo_man/FOO/master/chu.zip"
                        ),
                    Util.Container(
                        id="extract",
                        arg="chu/"
                        )
                    ],
                "BAR" : [
                    Util.Container(
                        id="dest",
                        arg="bar.bin"
                        ),
                    Util.Container(
                        id="url",
                        arg="https://foohub.com/foo_man/FOO/master/bar.bin"
                        )
                    ]
                }),
            }))

    def test_empty_project(self):
        self.create_parser()
        self.parse_lines(
            "; This is a comment",
            "# This is also a comment",
            "   ; This comment is indented",
            ":project MyProject",
            ":end",
            )

        self.verify_project(Util.Container(**{
            "name" : "MyProject",
            "layers" : [],
            "packages" : [],
            "dependencies" : []
            }))

    def test_layers(self):
        self.create_parser()
        self.parse_lines(
            ":project Breakfast",
            "    :layer cereal",
            "        variant SugarFlakes",
            "    :end",
            "    :layer fruit",
            "        variant Apple",
            "        variant Banana",
            "        variant Pear",
            "        suffix .yum",
            "    :end",
            "    :layer drink",
            "        prefix ../liquids/",
            "        variant Apple",
            "        variant Orange",
            "        variant Cow",
            "        suffix _Juice.txt",
            "    :end",
            ":end",
            )

        self.verify_project(Util.Container(**{
            "name" : "Breakfast",
            "layers" : [
                Util.Container(
                    name="cereal",
                    variants=[
                        Util.Container(
                            name="SugarFlakes",
                            filename="cereal_SugarFlakes.cfg"
                            )
                        ]
                    ),
                Util.Container(
                    name="fruit",
                    variants=[
                        Util.Container(
                            name="Apple",
                            filename="fruit_Apple.yum"
                            ),
                        Util.Container(
                            name="Banana",
                            filename="fruit_Banana.yum"
                            ),
                        Util.Container(
                            name="Pear",
                            filename="fruit_Pear.yum"
                            )
                        ]
                    ),
                Util.Container(
                    name="drink",
                    variants=[
                        Util.Container(
                            name="Apple",
                            filename="../liquids/Apple_Juice.txt"
                            ),
                        Util.Container(
                            name="Orange",
                            filename="../liquids/Orange_Juice.txt"
                            ),
                        Util.Container(
                            name="Cow",
                            filename="../liquids/Cow_Juice.txt"
                            )
                        ]
                    )
                ],
            "packages" : [],
            "dependencies" : []
            }))

    def test_name_whitespace(self):
        self.create_parser()
        self.parse_lines(
            ":project \tMy_Project ",
            ":end",
            )

        self.verify_project(Util.Container(**{
            "name" : "My_Project",
            "layers" : [],
            "packages" : [],
            "dependencies" : []
            }))

    def test_packages(self):
        self.create_parser()
        self.parse_lines(
            ":project MyProject",
            "    :package package1.gman",
            "    :package ./package2.mfg",
            ":end"
            )

        self.verify_project(Util.Container(**{
            "name" : "MyProject",
            "layers" : [],
            "packages" : [
                Util.Container(
                    filename="package1.gman",
                    file_root=Project.ROOT.SOURCE,
                    module_root=Project.ROOT.SOURCE,
                    module_id=None
                    ),
                Util.Container(
                    filename="./package2.mfg",
                    file_root=Project.ROOT.SOURCE,
                    module_root=Project.ROOT.SOURCE,
                    module_id=None
                    )
                ],
            "dependencies" : []
            }))

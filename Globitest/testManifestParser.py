#/usr/bin/env python
"""
    globifest/globitest/testManifestParser.py - Tests for ManifestParser module

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

from GlobifestLib import Log, LineReader, Manifest, ManifestParser, Util
from Globitest import Helpers

def create_empty_manifest_container():
    return Util.Container(
        aux_files = [],
        prv_defines = [],
        prv_includes = [],
        pub_defines = [],
        pub_includes = [],
        sources = []
    )

class TestManifestParser(unittest.TestCase):

    def setUp(self):
        self.pipe = io.StringIO()
        Log.Logger.set_err_pipe(self.pipe)
        self.trace_msg = None

    def doCleanups(self):
        Log.Logger.set_err_pipe(sys.stderr)
        if not self._outcome.success:
            if self.trace_msg:
                print("TRACE:")
                print(self.trace_msg)
            if hasattr(self, "parser"):
                print("PARSER DEBUG LOG:")
                print(self.parser.get_debug_log())
            if hasattr(self, "pipe") and self.pipe:
                print("ERRORS:")
                print(self.pipe.getvalue().rstrip())
            if hasattr(self, "manifest"):
                print("PARSED MANIFEST:")
                print(self.manifest)
            else:
                print("NO MANIFEST!")

        # Unreference the objects in reverse order
        if hasattr(self, "reader"):
            del self.reader
        if hasattr(self, "parser"):
            del self.parser
        if hasattr(self, "manifest"):
            del self.manifest
        if hasattr(self, "pipe"):
            del self.pipe

    def create_parser(self, configs = Util.Container()):
        # The manifest and reader are not under test, but simple enough to use directly
        self.manifest = Helpers.new_manifest()
        self.configs = Helpers.new_configset(configs)
        self.parser = ManifestParser.new(self.manifest, self.configs, debug_mode=True, validate_files=False)

        # The reader is not under test, but it provides a good way to feed strings to the parser
        self.reader = LineReader.new(self.parser)

    def parse_lines(self, *args):
        file = Helpers.new_file("\n".join(args))
        self.reader._read_file_obj(file)

    def verify_manifest(self, expected):
        diff = expected.get_diff(self.manifest.get_output())
        if diff != Util.Container():
            print("UNMATCHED FIELDS:{}\n".format(diff))
            self.fail()

    def test_basic_manifest(self):
        self.create_parser()
        self.parse_lines(
            "; This is a comment",
            "# This is also a comment",
            "   ; This comment is indented",
            ":sources",
            "   abc_module.c"
            )

        expected = create_empty_manifest_container()
        expected.sources = ["abc_module.c"]
        self.verify_manifest(expected)

    def test_conditional_compact1(self):
        for data in [
            ("1", ["a"]),
            ("2", ["b"]),
            ("3", ["c"])
            ]:
            self.trace_msg = "sel = " + data[0]
            self.create_parser(Util.Container(sel = data[0]))
            self.parse_lines(
                ":sources",
                ":if(sel=1)",
                "a",
                ":elif(sel=2)",
                "b",
                ":else",
                "c",
                ":end"
                )

            expected = create_empty_manifest_container()
            expected.sources = data[1]
            self.verify_manifest(expected)

    def test_conditional_compact2(self):
        for data in [
            ("1", ["a1","a2"]),
            ("2", ["b1","b2"]),
            ("3", ["c1","c2"])
            ]:
            self.trace_msg = "sel = " + data[0]
            self.create_parser(Util.Container(sel = data[0]))
            self.parse_lines(
                ":sources",
                ":if(sel=1)",
                "    a1",
                "    a2",
                ":elif(sel=2)",
                "    b1",
                "    b2",
                ":else",
                "    c1",
                "    c2",
                ":end"
                )

            expected = create_empty_manifest_container()
            expected.sources = data[1]
            self.verify_manifest(expected)

    def test_conditional_long1(self):
        for data in [
            ("1", ["a"]),
            ("2", ["b"]),
            ("3", ["c"]),
            ("4", ["d"])
            ]:
            self.trace_msg = "sel = " + data[0]
            self.create_parser(Util.Container(sel = data[0]))
            self.parse_lines(
                ":sources",
                ":if",
                "    (",
                "    sel=1",
                "    )",
                "    a",
                ":elif",
                "    (",
                "    sel=2",
                "    )",
                "    b",
                ":elif",
                "    (",
                "    sel==3",
                "    )",
                "    c",
                ":else",
                "    d",
                ":end"
                )

            expected = create_empty_manifest_container()
            expected.sources = data[1]
            self.verify_manifest(expected)

    def test_conditional_long2(self):
        for data in [
            ("1", ["a1","a2"]),
            ("2", ["b1","b2"]),
            ("3", ["c1","c2"]),
            ("4", ["d1","d2"])
            ]:
            self.trace_msg = "sel = " + data[0]
            self.create_parser(Util.Container(sel = data[0]))
            self.parse_lines(
                ":sources",
                ":if",
                "    (",
                "    sel=1",
                "    )",
                "    a1",
                "    a2",
                ":elif",
                "    (",
                "    sel=2",
                "    )",
                "    b1",
                "    b2",
                ":elif",
                "    (",
                "    sel==3",
                "    )",
                "    c1",
                "    c2",
                ":else",
                "    d1",
                "    d2",
                ":end"
                )

            expected = create_empty_manifest_container()
            expected.sources = data[1]
            self.verify_manifest(expected)

    def test_conditional_nested_complex(self):
        for data in [
            ("1","1", ["a_top","a1"], ["top_hdr","a1_hdr"]),
            ("1","2", ["a_top","a2"], ["top_hdr","a2_hdr"]),
            ("1","3", ["a_top","a3"], ["top_hdr","a3_hdr"]),
            ("2","1", ["b_top","b1"], ["top_hdr","b1_hdr"]),
            ("2","2", ["b_top","b2"], ["top_hdr","b2_hdr"]),
            ("2","3", ["b_top","b3"], ["top_hdr","b3_hdr"]),
            ("3","1", ["c_top","c1"], ["top_hdr","c1_hdr"]),
            ("3","2", ["c_top","c2"], ["top_hdr","c2_hdr"]),
            ("3","3", ["c_top","c3"], ["top_hdr","c3_hdr"])
            ]:
            self.trace_msg = "sel = " + data[0]
            self.create_parser(Util.Container(
                x=data[0],
                y=data[1]
                ))
            self.parse_lines(
                ":pub_includes",
                "    top_hdr",
                ":sources",
                ":if( x=1 )",
                "    a_top",
                "    :if( y=1 )",
                "        a1",
                "        :pub_includes",
                "            a1_hdr",
                "    :elif( y=2 )",
                "        a2",
                "        :pub_includes",
                "            a2_hdr",
                "    :else",
                "        a3",
                "        :pub_includes",
                "            a3_hdr",
                "    :end",
                ":elif( x=2 )",
                "    b_top",
                "    :if( y=1 )",
                "        b1",
                "        :pub_includes",
                "            b1_hdr",
                "    :elif( y=2 )",
                "        b2",
                "        :pub_includes",
                "            b2_hdr",
                "    :else",
                "        b3",
                "        :pub_includes",
                "            b3_hdr",
                "    :end",
                ":else",
                "    c_top",
                "    :if( y=1 )",
                "        c1",
                "        :pub_includes",
                "            c1_hdr",
                "    :elif( y=2 )",
                "        c2",
                "        :pub_includes",
                "            c2_hdr",
                "    :else",
                "        c3",
                "        :pub_includes",
                "            c3_hdr",
                "    :end",
                ":end",
                )

            expected = create_empty_manifest_container()
            expected.sources = data[2]
            expected.pub_includes = data[3]
            self.verify_manifest(expected)

    def test_empty_file(self):
        self.create_parser()
        self.parse_lines("")

        expected = create_empty_manifest_container()
        self.verify_manifest(expected)

    def test_flat_manifest(self):
        self.create_parser()
        self.parse_lines(
            ":prv_includes",
            "   .",
            ":pub_includes",
            "   include",
            "   xyz/lib",
            ":pub_defines",
            "   __ABC_MODULE_VER__=100",
            "   __ABC_LIST__",
            ":prv_defines",
            "   __xyz_static__",
            "   __xyz_nodeprecate__",
            ":sources",
            "   abc_module.c",
            "   abc_list.c",
            "   xyz/xyz_lib.c",
            ":aux_files",
            "   README.md",
            "   LICENSE",
            "   xyz/LICENSE",
            "   xyz/README.md"
            )

        expected = Util.Container(
            aux_files = ["README.md", "LICENSE", "xyz/LICENSE", "xyz/README.md"],
            prv_defines = ["__xyz_static__", "__xyz_nodeprecate__"],
            prv_includes = ["."],
            pub_defines = ["__ABC_MODULE_VER__=100", "__ABC_LIST__"],
            pub_includes = ["include", "xyz/lib"],
            sources = ["abc_module.c", "abc_list.c", "xyz/xyz_lib.c"]
        )
        self.verify_manifest(expected)

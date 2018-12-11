#/usr/bin/env python
"""
    globifest/globitest/testProject.py - Tests for Project module

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

from GlobifestLib import Project, Util

class TestProject(unittest.TestCase):

    def verify_configs(self, actual, expected):
        self.assertEqual(actual.get_diff(expected), Util.Container())

    def test_complex_set(self):
        prj = Project.new(err_fatal=True)
        self.assertIsNone(prj.get_name())
        prj.set_name("Complex Set")
        self.assertEqual(prj.get_name(), "Complex Set")

        prj.add_layer("layer1")
        prj.add_variant("layer1", "variant1.1", "l1_v1_1.cfg")
        prj.add_variant("layer1", "variant1.2", "l1_v1_2.cfg")
        prj.add_layer("layer2")
        prj.add_variant("layer2", "variant2.1", "l2_v2_1.cfg")

        self.assertEqual(prj.get_target("layer1", "variant1.1").filename, "l1_v1_1.cfg")
        self.assertEqual(prj.get_target("layer1", "variant1.2").filename, "l1_v1_2.cfg")
        self.assertEqual(prj.get_target("layer2", "variant2.1").filename, "l2_v2_1.cfg")

        prj.get_target("layer1", "variant1.1").config.cfg_a1 = "A1"
        prj.get_target("layer1", "variant1.1").config.cfg_b1 = "B1"
        prj.get_target("layer1", "variant1.2").config.cfg_a2 = "A2"
        prj.get_target("layer2", "variant2.1").config.cfg_c1 = "C1"

        self.verify_configs(
            prj.get_target("layer1", "variant1.1").config,
            Util.Container(
                cfg_a1="A1",
                cfg_b1="B1"
                )
            )
        self.verify_configs(
            prj.get_target("layer1", "variant1.2").config,
            Util.Container(
                cfg_a2="A2"
                )
            )
        self.verify_configs(
            prj.get_target("layer2", "variant2.1").config,
            Util.Container(
                cfg_c1="C1"
                )
            )

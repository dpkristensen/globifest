#/usr/bin/env python
"""
    globifest/globitest/testManifest.py - Tests for Manifest module

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

from GlobifestLib import Manifest
from Globitest import Helpers

class TestManifest(unittest.TestCase):

    def test_data(self):
        manifest = Manifest.new(Helpers.TEST_FNAME)

        manifest.add_type("type_a")
        manifest.add_type("type_b")
        manifest.add_type("type_c")

        manifest.add_entry("type_a", "a1")
        manifest.add_entry("type_a", "a2")

        manifest.add_entry("type_c", "c1")

        out = manifest.get_output()
        self.assertEquals(out, dict(
            type_a = ["a1", "a2"],
            type_b = [],
            type_c = ["c1"]
            ))

    def test_filename(self):
        manifest = Manifest.new("different_name.glst")
        self.assertEquals(manifest.get_filename(), "different_name.glst")

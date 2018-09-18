#/usr/bin/env python
"""
    globifest/globitest/testUtil.py - Tests for Util module

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
import unittest

from GlobifestLib import Util

class TestUtil(unittest.TestCase):

    def test_container1(self):
        container1 = Util.Container(
            a = 1,
            b = 2
            )
        container2 = Util.Container(
            b = 2,
            a = 1
            )
        self.assertEqual(container1._get_diff(container2), Util.Container())

    def test_container2(self):
        container1 = Util.Container(
            a = [1, 2, 3],
            b = 2
            )
        container2 = Util.Container(
            b = 2,
            a = [3, 2, 1]
            )
        self.assertEqual(container1._get_diff(container2), Util.Container())

    def test_container3(self):
        container1 = Util.Container(
            a = [1, 2, 3],
            b = 2
            )
        container2 = Util.Container(
            b = 2,
            a = [3, 2, 1, 4]
            )
        result = Util.Container(
            a = [4]
            )
        self.assertEqual(container1._get_diff(container2), result)

    def test_container4(self):
        container1 = Util.Container(
            a = [1, 2, 3, 4],
            b = 2
            )
        container2 = Util.Container(
            b = 2,
            a = [3, 2, 1]
            )
        result = Util.Container(
            a = [4]
            )
        self.assertEqual(container1._get_diff(container2), result)

    def test_container5(self):
        container1 = Util.Container(
            a = 1,
            b = 2
            )
        container2 = Util.Container(
            b = 2,
            c = 3
            )
        result = Util.Container(
            a = 1,
            c = 3
            )
        self.assertEqual(container1._get_diff(container2), result)

    def test_container6(self):
        container1 = Util.Container(
            a = [1, 2, 3],
            b = 2
            )
        container2 = Util.Container(
            b = 2,
            a = [3, 2, 1],
            c = [5, 6]
            )
        result = Util.Container(
            c = [5, 6]
            )
        self.assertEqual(container1._get_diff(container2), result)

    def test_container_copy(self):
        original = Util.Container(
            a = [1, 2],
            b = [3, 4]
            )
        shadow = copy.copy(original)
        self.assertEqual(original, shadow)

        # Verify shallow copy by modifying a member
        original.a[0] = 5
        self.assertEqual(original.a, [5, 2])
        self.assertEqual(shadow.a, [5, 2])

        # Verify member replacement
        original.a = [6, 7]
        self.assertEqual(original.a, [6, 7])
        self.assertEqual(shadow.a, [5, 2])

    def test_container_deepcopy(self):
        original = Util.Container(
            a = [1, 2],
            b = [3, 4]
            )
        shadow = copy.deepcopy(original)
        self.assertEqual(original, shadow)

        # Verify deep copy by modifying a member
        original.a[1] = 5
        self.assertEqual(original.a, [1, 5])
        self.assertEqual(shadow.a, [1, 2])

        # Verify member replacement
        original.a = [6, 7]
        self.assertEqual(original.a, [6, 7])
        self.assertEqual(shadow.a, [1, 2])

    def test_create_enum(self):
        testEnum = Util.create_enum("a", "b", "c", "d")
        self.assertEqual(testEnum.a, 0)
        self.assertEqual(testEnum.b, 1)
        self.assertEqual(testEnum.c, 2)
        self.assertEqual(testEnum.d, 3)
        self.assertEqual(4, testEnum.COUNT)

    def test_create_flag_enum(self):
        testBitField = Util.create_flag_enum("a", "b", "c", "d")
        self.assertEqual(testBitField.a, 0x1)
        self.assertEqual(testBitField.b, 0x2)
        self.assertEqual(testBitField.c, 0x4)
        self.assertEqual(testBitField.d, 0x8)
        self.assertEqual(0xf, testBitField.ALL)

    def test_power_of_2(self):
        expected = [1, 2, 4, 8]
        actual = Util.power_of_2([0, 1, 2, 3])
        self.assertEqual(expected, actual)

#/usr/bin/env python
"""
    globifest/Manifest.py - globifest Manifest object

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

import os

from GlobifestLib import Util

class Manifest:
    """
        Encapsulates all information about a manifest file
    """

    def __init__(self, fname, root=None):
        self.out = Util.Container()
        self.fname = fname
        self.configs = []
        if root is None:
            self.root = os.path.dirname(self.fname)
        else:
            self.root = root

    def __str__(self):
        outstr = "File: {}".format(self.fname)
        for label_key, label_value in self.out:
            outstr += "\n{}:".format(label_key)
            for entry in label_value:
                outstr += "\n  {}".format(entry)

        return outstr

    def add_config(self, config):
        """Add configuration information"""
        self.configs.append(config)

    def add_entry(self, typename, entry):
        """Add an entry of the given type"""
        if entry:
            self.out[typename] += [entry]

    def add_type(self, typename):
        """Add a table to the output for the given type"""
        self.out[typename] = []

    def get_configs(self):
        """Returns the associated configuration information"""
        return self.configs

    def get_filename(self):
        """Returns the filename of the manifest"""
        return self.fname

    def get_output(self):
        """Returns the output of the manifest"""
        return self.out

    def get_root(self):
        """Returns the root of the manifest where all the paths are"""
        return self.root

new = Manifest

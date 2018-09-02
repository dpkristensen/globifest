#/usr/bin/env python
"""
    globifest/ManifestReader.py - globifest Manifest Reader

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

from GlobifestLib import LineInfo, Log

class ManifestReader:
    """
        Reads data from a manifest file
    """

    def __init__(self, parser):
        self.parser = parser
        self.err_file_name = ""

    def error(self, action):
        Log.E("Could not {} manifest{}".format(action, self.err_file_name))

    def read_file_by_name(self, fname):
        self.err_file_name = " '{}'".format(fname)
        try:
            with open(fname, "r") as manifest_file:
                self._read_file_obj(manifest_file)
        except EnvironmentError:
            # Catch all external exceptions, so GlobifestException is passed up
            self.error("open")

    def _read_file_obj(self, manifest_file):
        line_count = 0
        manifest = self.parser.get_manifest()
        try:
            for line_text in manifest_file:
                line_count += 1
                line_info = LineInfo.new(manifest, line_count, line_text.lstrip().rstrip())
                self.parser.parse(line_info)
            self.parser.parse_end()
        except EnvironmentError:
            self.error("read from")

new = ManifestReader

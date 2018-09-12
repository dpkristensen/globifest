#/usr/bin/env python
"""
    globifest/LineReader.py - globifest Line Reader

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

class LineReader:
    """
        Reads lines of data from a file
    """

    def __init__(self, parser):
        self.parser = parser
        self.err_file_name = ""

    def error(self, action):
        """Log an error"""
        Log.E("Could not {} {}".format(action, self.err_file_name))

    def read_file_by_name(self, fname):
        """Read a file by name"""
        self.err_file_name = " '{}'".format(fname)
        try:
            with open(fname, "r") as manifest_file:
                self._read_file_obj(manifest_file)
        except EnvironmentError:
            # Catch all external exceptions, so GlobifestException is passed up
            self.error("open")

    def _read_file_obj(self, file_obj):
        """Read from a file-like object"""
        line_count = 0
        target = self.parser.get_target()
        try:
            for line_text in file_obj:
                line_count += 1
                line_info = LineInfo.new(target, line_count, line_text.lstrip().rstrip())
                self.parser.parse(line_info)
            self.parser.parse_end()
        except EnvironmentError:
            self.error("read from")

new = LineReader

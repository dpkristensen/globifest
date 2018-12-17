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

class OpenFileCM(object):
    """
        Context manager for opening a file

        This is differentiated from the normal "with open() as f" usage by only
        catching the exception in the open() call itself, not any exceptions
        handled in the body.
    """

    def __init__(self, filename, mode):
        self.file = None
        self.err_msg = "Internal error"
        self.filename = filename
        self.mode = mode

    def __bool__(self):
        return bool(self.file)

    def __nonzero__(self):
        return bool(self.file)

    def __enter__(self):
        try:
            self.file = open(self.filename, self.mode)
        except EnvironmentError as e:
            self.err_msg = e.strerror()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.file:
            self.file.close()

    def get_file(self):
        """Return the file object"""
        return self.file

    def get_err_msg(self):
        """Return the error message (only valid if an error occurred)"""
        return self.err_msg

class ReadLineInfoIter(object):
    """
        Iterator for reading lines from a file

        This allows reading lines one at a time iteratively, along with
    """

    def __init__(self, file, target):
        self.file = file
        self.read_ok = True
        self.line_count = 0
        self.err_msg = "Internal error"
        self.target = target

    def __bool__(self):
        return self.read_ok

    def __nonzero__(self):
        return self.read_ok

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        """Return LineInfo for the next line in the file, or None on EOF"""
        try:
            text = self.file.readline()
        except EnvironmentError as e:
            self.err_msg = e.strerror()
            self.read_ok = False
            raise StopIteration
        else:
            self.line_count += 1
            if not text:
                # EOF
                raise StopIteration

            return LineInfo.new(self.target, self.line_count, text.lstrip().rstrip())

    def get_err_msg(self):
        """Return the error message (only valid if an error occurred)"""
        return "{}:{} {}".format(self.target.get_filename(), self.line_count, self.err_msg)

class LineReader:
    """
        Reads lines of data from a file
    """

    def __init__(self, parser):
        self.parser = parser
        self.err_file_name = ""

    def error(self, action, sys_msg):
        """Log an error"""
        Log.E("Could not {} {}: {}".format(action, self.err_file_name, sys_msg))

    def read_file_by_name(self, fname):
        """Read a file by name"""
        self.err_file_name = " '{}'".format(fname)

        with OpenFileCM(fname, "r") as file_mgr:
            if file_mgr:
                self._read_file_obj(file_mgr.get_file())
            else:
                self.error("open", file_mgr.get_err_msg())

    def _read_file_obj(self, file_obj):
        """Read from a file-like object"""
        reader = ReadLineInfoIter(file_obj, self.parser.get_target())
        for line_info in reader:
            self.parser.parse(line_info)

        if not reader:
            self.error("read from", reader.get_err_msg())
        else:
            self.parser.parse_end()

new = LineReader

#/usr/bin/env python
"""
    globifest/Log.py - globifest Logger

    This file contains logging functions.

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

import inspect
import io
import os
import sys

from GlobifestLib import Util

# Level constants
LEVEL = Util.create_enum(
    "NONE",
    "INFO",
    "DEBUG",
    "EXTREME",

    "COUNT"
    )

# Error types
ERROR = Util.create_enum(
    "BUILD",
    "INPUT",
    "RUNTIME",

    "COUNT"
    )

class GlobifestException(Exception):
    """Exception class used for all exceptions generated by Globifest"""

    def __init__(self, err_type, msg):
        Exception.__init__(self)
        self.err_type = err_type
        self.msg = msg

    def __str__(self):
        return self.msg

    def get_type(self):
        """Returns the ERROR type"""
        return self.err_type + 1

class LoggerClass(object):
    """
        Encapsulates functionality for logging
    """

    def __init__(self):
        self.verbosity_level = 0
        self.out_pipe = sys.stdout
        self.err_pipe = sys.stderr

    def has_level(self, level):
        """Static method"""
        return self.verbosity_level >= level

    def log_msg(self, level, msg):
        """Prints the message if it is allowed by the verbosity level"""
        if self.has_level(level):
            print(msg, file=self.out_pipe)

    def log_error(self, msg, err_type=ERROR.BUILD, is_fatal=True, frame=Util.get_stackframe(2)):
        """Prints and raises an error message"""
        debug_info = ""
        local_variables = None
        if frame and self.has_level(LEVEL.EXTREME):
            f_info = inspect.getframeinfo(frame)
            fname = os.path.basename(f_info.filename)
            debug_info = "[{}@{:d}] ".format(fname, f_info.lineno)
            local_variables = frame.f_locals
        print("{}Error: {}\n".format(debug_info, msg), file=self.err_pipe)
        if local_variables:
            print("Locals:")
            print(local_variables)
        if is_fatal:
            raise GlobifestException(err_type, msg)

    def set_err_pipe(self, pipe):
        """Set the pipe for error messages"""
        self.err_pipe = pipe

    def set_level(self, level):
        """Set the minimum verbosity level for log messages"""
        self.verbosity_level = level

    def set_out_pipe(self, pipe):
        """Set the pipe for non-error messages"""
        self.out_pipe = pipe

Logger = LoggerClass()

def E(msg, err_type=ERROR.BUILD, is_fatal=True):
    """Log an error"""
    Logger.log_error(msg, err_type, is_fatal, Util.get_stackframe(3))


def I(msg):
    """Log an informational message"""
    Logger.log_msg(LEVEL.INFO, msg)


def D(msg):
    """Log a debug message"""
    Logger.log_msg(LEVEL.DEBUG, msg)

def X(msg):
    """Log an extremely detailed message"""
    Logger.log_msg(LEVEL.EXTREME, msg)

class CaptureStdout(object):
    """
        Context Manager class to capture stdout from python statements
    """
    def __init__(self, debuggable, header):
        self.debuggable = debuggable
        self.header = header
        self.orig_stdout = sys.stdout
        self.stream = io.StringIO()

    def __enter__(self):
        sys.stdout = self.stream
        return self

    def __exit__(self, var_type, var_value, traceback):
        if self.stream.getvalue():
            # Only print if something was captured
            self.debuggable.debug(self.header)
            for line in self.stream.getvalue().splitlines():
                self.debuggable.debug(line)
        del self.stream
        sys.stdout = self.orig_stdout

class Debuggable(object):
    """
        Implements shared logic for debugging in a specific context
    """

    def __init__(self, debug_mode=False):
        """
            Initialize the class
        """
        self._debuggable = Util.Container(
            enabled=debug_mode,
            text=""
            )

    def debug(self, debug_text):
        """Write text to the debug log"""
        if self._debuggable.enabled:
            self._debuggable.text += "\n  " + debug_text

    def link_debug_log(self, parent):
        """Link this object's debug log to the parent"""
        #pylint: disable=W0212
        self._debuggable = parent._debuggable

    def get_debug_mode(self):
        """Return whether debugging is enabled for this object"""
        return self._debuggable.enabled

    def get_debug_log(self):
        """Return the cached debug log from this object"""
        return self._debuggable.text

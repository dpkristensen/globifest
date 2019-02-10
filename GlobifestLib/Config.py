#/usr/bin/env python
"""
    globifest/Config.py - globifest Configuration

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

from GlobifestLib import \
    Log, \
    Settings, \
    Util

class Config(object):
    """
        Encapsulates configuration values stored in a file.

        See config-format.md for further details.
    """

    def __init__(self, filename="", err_ctx=Log.ERROR.RUNTIME, err_fatal=False):
        self.err_ctx = err_ctx
        self.err_fatal = err_fatal
        self.filename = filename

        self.configs = Util.Container() # Initially empty

        # Parallel containers for metadata associated with configs
        self.comments = Util.Container() # 0-1:1 with configs
        self.lines = Util.Container() # 1:1 with configs

        self.settings = None

    def add_value(self, line, ident, value):
        """
            Add a new configuration value

            @note Parameter type validation does not occur here because the definition is unknown.
                But the line information is included so that if an error is found, the setting
                can be referenced.
        """

        if ident in self.configs:
            self.log_error("Duplicate value {} at {}".format(ident, line))
        self.configs[ident] = value
        self.lines[ident] = line

    def get_filename(self):
        """Returns the filename where the project is defined"""
        return self.filename

    def get_comment(self, ident):
        """Returns the comment associated with ident, or empty string if none"""
        return self.comments.get(ident, "")

    def get_settings(self):
        """Returns a Settings object containing these values"""
        if self.settings is None:
            self.settings = Settings.new(self.configs)
        return self.settings

    def set_comment(self, line, ident, text):
        """Sets a comment to be associated with ident"""
        if ident in self.comments:
            self.log_error("Cannot change comment for {} at {}".format(ident, line))
        self.comments[ident] = text

    def log_error(self, msg):
        """
            Log an error

            @note The error may not be fatal, so it should be handled as well.
        """
        Log.E(msg, err_type=self.err_ctx, is_fatal=self.err_fatal, stackframe=3)

new = Config

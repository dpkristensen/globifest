#/usr/bin/env python
"""
    globifest/StatefulParser.py - globifest Stateful Parser

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

from GlobifestLib import Log, StateMachine, Util

PARSE_STATUS = Util.create_enum(
    "INCOMPLETE",
    "FINISHED",
    "ERROR"
    )

FLAGS = Util.create_flag_enum(
    "MULTI_LEVEL",
    "DEBUG"
    )

class StatefulParser(StateMachine.Base):
    """
        Helper class for parsing text using a state machine
    """

    def __init__(self, text="", flags=0):
        """
            Initialize the class

            @param text Initial text to add to the parser
            @type text str
        """
        StateMachine.Base.__init__(self, bool(flags & FLAGS.DEBUG))

        self.flags = flags
        self.text = text
        self.last_parsed_text = ""
        self.parsed_text = ""
        self.status = PARSE_STATUS.INCOMPLETE
        self.err_line = 0
        self.loop_count = 0

    def error(self, text):
        """
            Logs a non-fatal error and sets the parse status
        """
        err_text = text
        if self.is_flag_set(FLAGS.DEBUG):
            frame = Util.get_stackframe(2)
            if frame:
                err_text = err_text + "\n    @{}:{}".format(
                    frame.f_code.co_filename,
                    frame.f_lineno
                    )
        Log.E(err_text, is_fatal=False)
        self.status = PARSE_STATUS.ERROR

    def get_parsed_text(self):
        """Returns all of the text which was matched by the machine"""
        return self.parsed_text

    def get_last_parsed_text(self):
        """Returns the last text which was parsed by the machine"""
        return self.last_parsed_text

    def get_remaining_text(self):
        """Returns the text which has not been parsed"""
        return self.text

    def get_status(self):
        """Returns parse status"""
        return self.status

    def is_flag_set(self, flag):
        """Returns whether flag is set"""
        return (self.flags & flag) != 0

    def on_text(self):
        """
            Default text handler

            Concrete class should override this to handle parsed text
        """
        pass

    def parse(self, new_text=""):
        """
            Parse text in a loop

            Calls the on_done(text) handler, which must return True to keep parsing, or False to
            stop.

            @return PARSE_STATUS
        """
        if self.get_status() == PARSE_STATUS.FINISHED:
            self.error("Received data after finished parsing")

        self.text += new_text

        self.debug("--parse--")
        self.debug("state={}".format(self._get_new_state()))
        self._debug_log_text()

        while self.status != PARSE_STATUS.ERROR:
            self.loop_count += 1
            self.debug("--loop {}--".format(self.loop_count))

            prev_text = self.text

            # Call the concrete implementation to parse it
            self.on_text()
            self._debug_log_text()

            if self._do_state_transition():
                # Parse again on state change
                continue

            if self.text != prev_text:
                # Parse again on change to remaining text
                continue

            if self.status == PARSE_STATUS.ERROR:
                # Stop on error, leave text as unparsed
                break

            if self.status == PARSE_STATUS.FINISHED:
                # Parsed all required data
                break

            # No state change, so add all remaining text as parsed
            self._append_parsed_text(self.text)
            self.text = ""
            self.debug("text->parsed")

            if not self.text:
                # Ran out of data to parse
                break

        return self.status

    def _append_parsed_text(self, text):
        self.last_parsed_text = text
        self.parsed_text += text

    def _complete_parse(self):
        self.status = PARSE_STATUS.FINISHED
        self.debug("--end--")

    def _debug_log_text(self):
        self.debug("text=\"{}\", parsed=\"{}\"".format(self.text, self.parsed_text))

Base = StatefulParser

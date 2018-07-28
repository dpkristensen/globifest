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

from GlobifestLib import StatefulParser, Util

BOUNDED_STATE = Util.create_enum(
    "LBOUND",
    "RBOUND",
    "DONE"
    )

class BoundedStatefulParser(StatefulParser.Base):
    """
        Parser which extracts text between two boundary characters
    """

    def __init__(self, text, lbound, rbound=None, flags=0):
        StatefulParser.Base.__init__(self, text, flags)

        self.lbound = lbound
        if rbound is None:
            self.rbound = lbound
        else:
            self.rbound = rbound

        self._set_state(BOUNDED_STATE.LBOUND)
        self.stack_level = 0

        self._debug("L=\"{}\" R=\"{}\"".format(self.lbound, self.rbound))

        if len(text) != 0:
            self.parse()

    def is_multi_level(self):
        return self.is_flag_set(StatefulParser.FLAGS.MULTI_LEVEL)

    def on_text(self):
        if self._get_state() == BOUNDED_STATE.DONE:
            # Stop if done
            self._complete_parse()
            return
        if self.text == "":
            # Nothing to parse
            return

        lpos = self.text.find(self.lbound)
        rpos = self.text.find(self.rbound)

        self._debug("lpos={} rpos={}".format(lpos, rpos))
        if (lpos < 0) and (rpos < 0):
            # Neither boundary is present
            if (self.parsed_text == "") and (self._get_state() == BOUNDED_STATE.LBOUND):
                # A boundary should be the first thing we find
                self.error("Unexpected text '{}'".format(self.text))
            return

        if self._get_state() == BOUNDED_STATE.LBOUND:
            if (rpos >= 0 ) and (rpos < lpos):
                # Exiting an inner level
                self.pop_stack(rpos, self.rbound, True)
                return
            elif lpos >= 0:
                # Entering new level, include boundary only for inner levels
                self.push_stack(lpos, self.lbound)
                self._set_state(BOUNDED_STATE.RBOUND)
                return
            else:
                # Input prior to the boundary is illegal
                self.error("Expected '{}'".format(self.lbound))
        elif self._get_state() == BOUNDED_STATE.RBOUND:
            if (lpos >= 0 ) and (lpos < rpos):
                # Entering an inner level
                self.push_stack(lpos, self.lbound)
                return
            elif rpos >= 0:
                # Exiting level, include boundary only for inner levels
                self.pop_stack(rpos, self.rbound, (self.stack_level > 1))
                if self.stack_level == 0:
                    self._set_state(BOUNDED_STATE.DONE)
                return
        else:
            # This should never happen
            self.error("Unexpected state {}".format(self._get_state()))

    def pop_stack(self, boundary_pos, boundary, include_boundary):
        if self.stack_level <=0:
            self.error("Unexpected {}".format(boundary))
        else:
            # Extract left side up to boundary into parsed_text
            pos = boundary_pos
            if include_boundary:
                pos += 1
            if pos >= 0:
                self._append_parsed_text(self.text[:pos])
            else:
                self.error("Internal error: p={} b=\"{}\"".format(pos, boundary))

            # Move start pointer up to just past boundary
            self.text = self.text[boundary_pos + 1:]
            self.stack_level -= 1
        if self.stack_level == 0:
            self.new_state = BOUNDED_STATE.DONE
        self._debug("pop L={}".format(self.stack_level))

    def push_stack(self, boundary_pos, boundary):
        if self.stack_level == 0:
            if boundary_pos == 0:
                # Entering outer level, just cut off the boundary
                self.text = self.text[boundary_pos + 1:]
                self.stack_level += 1
            else:
                self.error("Unexpected text before {}".format(boundary))
        elif (not self.is_multi_level()) or (self.stack_level <= 0):
            self.error("Unexpected {}".format(boundary))
        else:
            # Extract left side up to (and including) boundary into parsed_text
            if boundary_pos >= 0:
                self._append_parsed_text(self.text[:boundary_pos+1])
            else:
                self.error("Internal error: p={} b=\"{}\"".format(pos, boundary))

            # Move start pointer up to just past boundary
            self.text = self.text[boundary_pos+1:]
            self.stack_level += 1
        self._debug("push L={}".format(self.stack_level))

new = BoundedStatefulParser
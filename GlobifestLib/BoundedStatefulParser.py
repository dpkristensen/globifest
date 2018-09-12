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

        @note This parser also tracks strings, which override boundary detection
    """

    def __init__(self, text, lbound, rbound=None, flags=0, string_delims="\"'", string_escape="\\"):
        StatefulParser.Base.__init__(self, text, flags)

        # Set search parameters
        self.lbound = lbound
        if rbound is None:
            self.rbound = lbound
        else:
            self.rbound = rbound
        self.string_is_bound = lbound in string_delims
        self.string_delims = string_delims
        self.string_escape = string_escape

        # Set state parameters
        self._set_state(BOUNDED_STATE.LBOUND)
        self.stack_level = 0
        self.string_char = None
        self.new_state = self._get_state()

        self._debug("L=\"{}\" R=\"{}\"".format(self.lbound, self.rbound))
        self._debug("STRD={} STRE={}".format(self.string_delims, self.string_escape))

        if text:
            self.parse()

    def is_multi_level(self):
        """Returns whether FLAGS.MULTI_LEVEL is set."""
        return self.is_flag_set(StatefulParser.FLAGS.MULTI_LEVEL)

    def has_lbound(self):
        """Return whether the L bound has been found"""
        return self._get_state() != BOUNDED_STATE.LBOUND

    def on_text(self):
        """Handle text parsed from the caller."""
        if self._get_state() == BOUNDED_STATE.DONE:
            # Stop if done
            self._complete_parse()
            return
        if self.text == "":
            # Nothing to parse
            return

        # TODO: Optimize loop to find in one pass?
        lpos = self.text.find(self.lbound)
        rpos = self.text.find(self.rbound)
        if self.string_char is None:
            # If no string is started, look for the earliest delimeter
            strd_pos = -1
            for delim in self.string_delims:
                dpos = self.text.find(delim)
                if strd_pos == -1:
                    strd_pos = dpos
                elif (dpos >= 0) and (dpos < strd_pos):
                    strd_pos = dpos
        else:
            # Use the previous delimeter if a string is started
            strd_pos = self.text.find(self.string_char)
        stre_pos = self.text.find(self.string_escape)
        self._debug("lpos={} rpos={} sdpos={} sepos={}".format(lpos, rpos, strd_pos, stre_pos))

        # Check string logic first, since it overrides boundary logic
        if self.string_char is not None:
            # String has been started; end string before returning to boundary logic
            if strd_pos >= 0:
                # String delimiter is found
                self._debug("Append string")
                if (stre_pos >= 0) and ((stre_pos + 1) == strd_pos):
                    # Escaped delimiter, skip
                    self._append_parsed_text(self.text[:strd_pos + 1])
                    self.text = self.text[strd_pos + 1:]
                    return
                else:
                    self._debug("End string")
                    self.string_char = None
                    if not self.string_is_bound:
                        # If the string is not the boundary, consider it parsed here
                        self._append_parsed_text(self.text[:strd_pos + 1])
                        self.text = self.text[strd_pos + 1:]
                        return
            else:
                # No need to check string_is_bound, since no boundary to process either way.
                self._debug("Append whole string")
                self._append_parsed_text(self.text)
                self.text = ""
                return

        elif strd_pos >= 0:
            if (lpos >= 0) and (strd_pos > lpos):
                # String begins after the left boundary
                pass
            elif (rpos >= 0) and (strd_pos > rpos):
                # String begins after the right boundary
                pass
            else:
                # Not in a string; but one is being started
                self.string_char = self.text[strd_pos]
                self._debug("Enter string: {}".format(self.string_char))
                if not self.string_is_bound:
                    # If the string is not the boundary, consider it parsed here
                    self._append_parsed_text(self.text[:strd_pos + 1])
                    self.text = self.text[strd_pos + 1:]
                    return

        # Check boundary logic
        if (lpos < 0) and (rpos < 0):
            # Neither boundary is present
            if (self.parsed_text == "") and (self._get_state() == BOUNDED_STATE.LBOUND):
                # A boundary should be the first thing we find
                self.error("Unexpected text '{}'".format(self.text))
            return

        if self._get_state() == BOUNDED_STATE.LBOUND:
            if (rpos >= 0) and (rpos < lpos):
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
            if (lpos >= 0) and (lpos < rpos):
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
        """Reduce the number of nesting levels by one by exiting a boundary"""
        if self.stack_level <= 0:
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
        """Increase the number of nesting levels by one by entering a boundary"""
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
                self.error("Internal error: p={} b=\"{}\"".format(boundary_pos, boundary))

            # Move start pointer up to just past boundary
            self.text = self.text[boundary_pos+1:]
            self.stack_level += 1
        self._debug("push L={}".format(self.stack_level))

new = BoundedStatefulParser

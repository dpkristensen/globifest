#/usr/bin/env python
"""
    globifest/Matcher.py - globifest Matcher

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

class Matcher:
    """
        Helper class to test regex matches in an if/else ladder
    """

    def __init__(self, text):
        self.found = False
        self.text = text
        self.result = None

    def __getitem__(self, idx):
        """Implementation of lookup using []"""
        return self.result.group(idx)

    def get_num_matches(self):
        """Returns the number of groups matched"""
        if not self.found:
            return 0
        return len(self.result.groups())

    def is_match(self, expr):
        """
            @type expr re.RegexObj
            @return whether regex_obj matches the text using re.RegexObj.match()
            @rtype bool
        """
        self.result = expr.match(self.text)
        self.found = bool(self.result)

        return self.found

    def is_fullmatch(self, expr):
        """
            @type expr re.RegexObj
            @return whether regex_obj matches the text using re.RegexObj.fullmatch()
            @rtype bool
        """
        self.result = expr.fullmatch(self.text)
        self.found = bool(self.result)

        return self.found

    def was_found(self):
        """Return whether a result was found"""
        return self.found

new = Matcher

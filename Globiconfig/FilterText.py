#/usr/bin/env python
"""
    globiconfig/FilterText.py - globifest Config FilterText Control

    Copyright 2019, Daniel Kristensen, Garmin Ltd, or its subsidiaries.
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

import tkinter

def TextFilter(_event=None):
    """Filter function for text input"""
    return None

class NumericFilter(object):
    """
        Class for numeric filtering

        This filter can only limit new input to the field, not validate the
        ending expression.
    """

    DIGITS = "0123456789"
    # Some control characters need special handlling
    CONTROL = ["BackSpace"]

    def __init__(self, signed=True, fractional=False):
        self.allow_always = self.DIGITS
        self.control_chars = self.DIGITS
        self.allow_once = ""
        if signed:
            self.allow_once += "-"
        if fractional:
            self.allow_once += "."
        self.text_var = None

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __call__(self, event=None):
        if event.char in self.DIGITS:
            return None
        if event.keysym in self.CONTROL:
            return None
        if not event.char:
            print("Error: Uncaught control symbol {}".format(event.keysym))
            return "break"
        if self.text_var:
            # Look for an instance in the text already
            text = self.text_var.get()
            if not any(filter_char in text for filter_char in self.allow_once):
                # Not present, allow
                return None
        elif event.char in self.allow_once:
            # Treat it as always allowed when no text var link
            return None
        return "break"

class Text(tkinter.Entry):
    """Filtering text control"""

    def __init__(self, master, **kwargs):
        tkinter.Entry.__init__(self, master=master, **kwargs)
        self.filter_fn = TextFilter
        self.bind("<KeyPress>", self.filter_fn)
        self.text_var = kwargs.get("textvariable", None)

    def set_filter(self, filter_fn):
        """Set the function which will do the filtering for this control"""

        # pylint: disable=W0143
        if self.filter_fn == filter_fn:
            return

        if isinstance(filter_fn, NumericFilter):
            # Link the text variable to the filter
            filter_fn.text_var = self.text_var

        def _filter_cb(event=None):
            return filter_fn(event)

        self.bind("<KeyPress>", _filter_cb)

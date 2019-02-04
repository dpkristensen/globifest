#/usr/bin/env python
"""
    globiconfig/CheckBoxText.py - globifest Config CheckBoxText Control

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
import tkinter.ttk

from Globiconfig import FilterText

STICKY_FILL = tkinter.N + tkinter.W + tkinter.E + tkinter.S

class Control(tkinter.Frame):
    """Text control with a checkbutton to control enable/disable"""

    def __init__(self, master, observer):
        tkinter.Frame.__init__(self, master=master)
        self.observer = observer

        self.grid_rowconfigure(0, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # Checkbox
        self.check_var = tkinter.BooleanVar()
        self.checkbox = tkinter.ttk.Checkbutton(
            self,
            text="",
            variable=self.check_var,
            offvalue=False,
            onvalue=True
            )
        self.checkbox.grid(row=0, column=0, sticky=STICKY_FILL)

        # Text box
        self.text_var = tkinter.StringVar()
        self.textbox = FilterText.Text(
            self,
            textvariable=self.text_var
            )
        self.textbox.grid(row=0, column=1, sticky=STICKY_FILL)

        # Bind write handler to this object
        def value_changed_cb(*args):
            """Binding method to call the observer"""
            self.observer((self.check_var.get(), self.text_var.get()))

        self.check_var.trace("w", value_changed_cb)
        self.text_var.trace("w", value_changed_cb)

    def get_text(self):
        """Return the text"""
        return self.text_var.get()

    def set_text_filter(self, filter_fn):
        """Set the function which will do the filtering for the text box"""
        self.textbox.set_filter(filter_fn)

    def set_value(self, enabled, text=""):
        """Set the value of the fields"""
        self.check_var.set(enabled)

        self.textbox.config(state=tkinter.NORMAL)
        self.text_var.set(text)
        if not enabled:
            self.textbox.config(state=tkinter.DISABLED)

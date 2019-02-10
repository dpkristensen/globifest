#/usr/bin/env python
"""
    globiconfig/CheckBoxCombo.py - globifest Config CheckBoxCombo Control

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

STICKY_FILL = tkinter.N + tkinter.W + tkinter.E + tkinter.S

class Control(tkinter.Frame):
    """Combo box control with a checkbutton to control enable/disable"""

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

        # Combo box
        self.combo_var = tkinter.StringVar()
        self.combo_box = tkinter.ttk.Combobox(
            self,
            textvariable=self.combo_var,
            height=1
            )
        self.combo_box.grid(row=0, column=1, sticky=STICKY_FILL)

        # Bind write handler to this object
        def value_changed_cb(*args):
            """Binding method to call the observer"""
            self.observer((self.check_var.get(), self.combo_var.get()))

        self.check_var.trace("w", value_changed_cb)
        self.combo_var.trace("w", value_changed_cb)

    def get_text(self):
        """Return the text"""
        return self.combo_var.get()

    def set_choices(self, values):
        """Set the choices available for the box"""
        self.combo_box.configure(values=values)

    def set_value(self, enabled, text=""):
        """Set the value of the fields"""
        self.check_var.set(enabled)

        self.combo_box.config(state="readonly")
        self.combo_var.set(text)
        if not enabled:
            self.combo_box.config(state=tkinter.DISABLED)

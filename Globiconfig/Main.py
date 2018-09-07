#/usr/bin/env python
"""
    globiconfig/Main.py - globifest Config Main Application

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

import tkinter
from tkinter import messagebox
from GlobifestLib import Util

ACCEL = Util.create_enum(
    "CONTROL"
    )

ACCELERATOR = [
    Util.Container(text="Ctrl", bind="Control")
    ]

G_ID = Util.create_enum(
    "FRM_MAIN"
    )

class App(object):
    """
        Main Application
    """

    def __init__(self):
        self.gui_root = tkinter.Tk()

        self.create_dialog()
        self.create_menu_bar()

    def add_menu_item(self, top_menu, cmd):
        # Add a single menu item to top_menu
        if cmd == "-":
            top_menu.add_separator()
            return

        text = cmd.t
        a_pos = text.find("&")
        if a_pos == -1:
            top_menu.add_command(label=text, command=cmd.f)
        else:
            a_key = text[a_pos+1]
            text = text[:a_pos] + text[a_pos+1:]
            a_type = cmd.get("a", ACCEL.CONTROL)
            a_text = "{}+{}".format(ACCELERATOR[a_type].text, a_key.upper())
            binding = "<{}-{}>".format(ACCELERATOR[a_type].bind, a_key.lower())
            top_menu.add_command(label=text, underline=a_pos, command=cmd.f, accelerator=a_text)
            self.gui_root.bind_all(binding, cmd.f)

    def add_menu_items(self, top_menu, cmd_list):
        # Add a lsit of menu items to top_menu
        for i in cmd_list:
            self.add_menu_item(top_menu, i)

    def create_dialog(self):
        tkinter.Frame(
            self.gui_root
            ).pack()

    def create_menu_bar(self):
        # Create the menu bar
        M = Util.Container

        top_menu = tkinter.Menu(self.gui_root)

        file_menu = tkinter.Menu(top_menu, tearoff=0)
        self.add_menu_items(file_menu, [
            M(t="&Open", f=self.on_menu_file_open),
            M(t="&Close", f=self.on_menu_file_close),
            "-",
            M(t="E&xit", f=self.on_menu_file_exit)
            ])
        top_menu.add_cascade(label="File", underline=0, menu=file_menu)

        self.add_menu_item(top_menu, M(t="About!", f=self.on_menu_about))

        self.gui_root.config(menu=top_menu)

    def on_menu_about(self, event=None):
        # Show the about dialog
        #pylint: disable=unused-argument
        tkinter.messagebox.showinfo(
            "About",
            "Globifest Configuration Utility\n\n"
            "Copyright 2018 by Daniel Kristensen, Garmin Ltd, or its Subsidiaries.\n\n"
            "Licensed under the BSD 3-Clause license; see LICENSE.md for details."
            )

    def on_menu_file_exit(self, event=None):
        # Exit the program
        #pylint: disable=unused-argument
        self.gui_root.quit()

    def on_menu_file_close(self, event=None):
        # Close the configuration
        #pylint: disable=unused-argument
        print("close")

    def on_menu_file_open(self, event=None):
        # Open a configuration file
        #pylint: disable=unused-argument
        print("open")

    def run(self):
        """Run the application, and return success"""

        self.gui_root.mainloop()
        return 0

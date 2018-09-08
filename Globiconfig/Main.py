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

PADDING = 5
STICKY_FILL = tkinter.N + tkinter.W + tkinter.E + tkinter.S
PANE_0_MINWIDTH = 100
PANE_1_MINWIDTH = 100
WINDOW_MINWIDTH = 300
WINDOW_MINHEIGHT = 200
DIVIDER_WIDTH = 8

assert (PANE_0_MINWIDTH + PANE_1_MINWIDTH) <= WINDOW_MINWIDTH

class App(object):
    """
        Main Application
    """

    def __init__(self):
        self.app_root = tkinter.Tk()
        self.app_root.title("Globiconfig")
        self.app_root.minsize(width=WINDOW_MINWIDTH, height=200)

        # Divide the window into two panes, whcih stretch according to the divider's size
        pane_divider = tkinter.PanedWindow(
            self.app_root,
            handlesize=DIVIDER_WIDTH,
            sashwidth=DIVIDER_WIDTH,
            sashrelief=tkinter.GROOVE
            )
        pane_divider.grid(sticky=STICKY_FILL)
        self.pane_0 = tkinter.Frame(pane_divider)
        pane_divider.add(self.pane_0, stretch="never")
        self.pane_1 = tkinter.Frame(pane_divider)
        pane_divider.add(self.pane_1, stretch="always")
        pane_divider.grid(sticky=STICKY_FILL)
        pane_divider.paneconfigure(self.pane_0, minsize=PANE_0_MINWIDTH)
        pane_divider.paneconfigure(self.pane_1, minsize=PANE_1_MINWIDTH)

        # Make the cell containing the pane divider autoresize, which in turn allows the
        # panes and their children resize.
        self.app_root.grid_columnconfigure(0, weight=1)
        self.app_root.grid_rowconfigure(0, weight=1)

        # Populate controls
        self.create_menu_bar()
        self.create_pane_0()
        self.create_pane_1()

        # Add some fake data for testing
        for i in [
                "FOO_SUPPORT",
                "BAZ_ADDRESS",
                "BAZ_SHIZZLE",
                "BAZ_RST_GPIO",
                "BAZ_RST_GPIO_PULL_CFG",
                "BAZ_IRQ_GPIO",
                "BAZ_IRQ_GPIO_PULL_CFG",
                "BAZ_IRQ_TRIGGER_CFG",
                "BAR_ID",
                "BAR_NIZZLE",
                "BAR_FORMAT"
            ]:
            self.cfg_list.insert(tkinter.END, i)
        self.set_description("Description goes here\non multiple lines!")

    def add_menu_item(self, top_menu, cmd):
        """Add a single menu item to top_menu"""
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
            self.app_root.bind_all(binding, cmd.f)

    def add_menu_items(self, top_menu, cmd_list):
        """"Add a lsit of menu items to top_menu"""
        for i in cmd_list:
            self.add_menu_item(top_menu, i)

    def create_menu_bar(self):
        """Create the menu bar"""
        M = Util.Container

        top_menu = tkinter.Menu(self.app_root)

        file_menu = tkinter.Menu(top_menu, tearoff=0)
        self.add_menu_items(file_menu, [
            M(t="&Open", f=self.on_menu_file_open),
            M(t="&Close", f=self.on_menu_file_close),
            "-",
            M(t="E&xit", f=self.on_menu_file_exit)
            ])
        top_menu.add_cascade(label="File", underline=0, menu=file_menu)

        self.add_menu_item(top_menu, M(t="About!", f=self.on_menu_about))

        self.app_root.config(menu=top_menu)

    def create_pane_0(self):
        """
            Create the controls on the left side of the window
        """
        # Auto-resize child objects to pane width
        self.pane_0.grid_columnconfigure(0, weight=1)

        # Navigation bar at the top; match the list width
        self.nav_bar = tkinter.LabelFrame(
            self.pane_0,
            text="Navigation Bar",
            padx=PADDING,
            pady=PADDING
            )
        self.nav_bar.grid(row=0, sticky=STICKY_FILL, padx=PADDING)

        # Create the top-level menu navigator
        home_btn = tkinter.Button(self.nav_bar, text="/", relief=tkinter.SUNKEN)
        home_btn.grid(sticky=tkinter.W)
        self.nav_btns = [home_btn]

        # Create the config list in a parent frame for layout
        cfg_frame = tkinter.Frame(self.pane_0)
        scrollbar = tkinter.Scrollbar(cfg_frame, orient=tkinter.VERTICAL)
        self.cfg_list = tkinter.Listbox(cfg_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.cfg_list.yview)
        self.cfg_list.grid(row=0, column=0, sticky=STICKY_FILL)
        scrollbar.grid(row=0, column=1, sticky=STICKY_FILL)
        cfg_frame.grid(row=1, padx=PADDING, pady=PADDING, sticky=STICKY_FILL)
        # Resize the list to match the window
        cfg_frame.grid_columnconfigure(0, weight=1)
        cfg_frame.grid_rowconfigure(0, weight=1)
        self.pane_0.grid_rowconfigure(1, weight=1)

    def create_pane_1(self):
        """
            Create the controls on the right side of the window
        """
        # Auto-resize child objects to pane width
        self.pane_1.grid_columnconfigure(0, weight=1)

        # Description area
        desc_frame = tkinter.LabelFrame(
            self.pane_1,
            text="Description",
            padx=PADDING,
            pady=PADDING
            )
        desc_frame.grid(row=1, sticky=STICKY_FILL, padx=PADDING)
        self.desc_txt = tkinter.Text(
            desc_frame,
            font="TkFixedFont",
            relief=tkinter.FLAT,
            bg=desc_frame.cget("background")
            )
        self.desc_txt.grid()
        self.set_description("")

    def on_menu_about(self, event=None):
        """Show the about dialog"""
        #pylint: disable=unused-argument
        msg = "\n".join([
            "Globifest Configuration Utility",
            "",
            "Copyright 2018 by Daniel Kristensen, Garmin Ltd, or its Subsidiaries.",
            "",
            "Licensed under the BSD 3-Clause license; see LICENSE.md for details."
            ])
        tkinter.messagebox.showinfo("About", msg)

    def on_menu_file_exit(self, event=None):
        """Exit the program"""
        #pylint: disable=unused-argument
        self.app_root.quit()

    def on_menu_file_close(self, event=None):
        """Close the configuration"""
        #pylint: disable=unused-argument
        print("close")

    def on_menu_file_open(self, event=None):
        """Open a configuration file"""
        #pylint: disable=unused-argument
        print("open")

    def run(self):
        """Run the application, and return success"""

        self.app_root.mainloop()
        return 0

    def set_description(self, text):
        """Set the text in the description box"""
        self.desc_txt.config(state=tkinter.NORMAL)
        self.desc_txt.delete(1.0, tkinter.END)
        self.desc_txt.insert(tkinter.END, text)
        self.desc_txt.config(state=tkinter.DISABLED)

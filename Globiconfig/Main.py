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

import os
import tkinter
import tkinter.ttk
import tkinter.messagebox

from GlobifestLib import Builder, DefTree, Log, ManifestParser, Util

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
DIVIDER_WIDTH = 4

assert (PANE_0_MINWIDTH + PANE_1_MINWIDTH) <= WINDOW_MINWIDTH

CFG_TAG = Util.create_enum(
    "MENU",
    "PARAM"
    )

def gui_child_sorter(children):
    """Sorter (PEP 265) for children to be shown in the config tree"""
    return sorted(children, key=DefTree.DefForest.ChildNameGetter())

def gui_param_sorter(params):
    """Sorter (PEP 265) for parameters to be shown in the config tree"""
    return sorted(params, key=DefTree.DefForest.ParamTextGetter())

class CfgTreeObserver(object):
    """Observer for DefForest to add items to the config tree"""

    def __init__(self, cfg_tree, param_tbl):
        # Links to objects owned by application
        self.cfg_tree = cfg_tree
        self.param_tbl = param_tbl

        # Temporary workspace variables
        self.param_tree = list()
        self.root_stack = list()
        self.counter_stack = list()
        self.level = 0

    def on_param(self, param):
        """Save parameters to be added after all children"""
        self.param_tree[-1].append(param)

    def on_scope_begin(self, title, description):
        """Add a child item"""
        # Add a new empty param tree level
        self.param_tree.append(list())

        self.level += 1
        if self.level == 1:
            # Only process parameters in the top scope
            return

        # Incrememt the counter; each child will be identified within its
        # parent level numerically: 1, 2, 3, etc...
        if self.counter_stack:
            self.counter_stack[-1] += 1
        else:
            self.counter_stack.append(0)

        # Join the counters together to form a unique IID representative of
        # its position in the tree: 1, 1_1, 2_1_3, etc...
        new_iid = "_".join(str(c) for c in self.counter_stack)

        if self.root_stack:
            parent = self.root_stack[-1]
        else:
            parent = ""

        # Add a new element to this tree level
        self.counter_stack.append(0)
        self.cfg_tree.insert(
            parent=parent,
            index="end",
            iid=new_iid,
            text=title,
            values=(description,),
            tags=(CFG_TAG.MENU,)
            )

        # Add the new IID to the root stack for children in this scope
        self.root_stack.append(new_iid)

    def on_scope_end(self):
        """Pop the current scope level"""
        self.level -= 1
        if self.level == 0:
            # Adjust parent for top-level parameters
            parent = ""
        else:
            parent = self.root_stack[-1]

        # Add all saved params, so that they appear below the child trees
        for p in self.param_tree[-1]:
            pid = p.param.get_identifier()
            self.param_tbl[pid] = p
            self.cfg_tree.insert(
                parent=parent,
                index="end",
                iid=pid,
                text=p.param.get_text(),
                values=(pid,),
                tags=(CFG_TAG.PARAM,)
                )

        # Clear the param tree for the next iteration
        self.param_tree.pop()

        if self.level == 0:
            # Only process parameters in top scope
            return

        self.root_stack.pop()
        self.counter_stack.pop()

class App(object):
    """
        Main Application
    """

    APP_TITLE = "Globiconfig"

    def __init__(self, project_file, out_dir):
        self.project_file = project_file
        self.out_dir = out_dir
        self.project = None
        self.param_tbl = Util.Container()
        self.settings_view_tbl = Util.Container()

        # Set up tkinter app root; this is not a super-class so the API is private
        self.app_root = tkinter.Tk()
        self.app_root.title(self.APP_TITLE)
        self.app_root.minsize(width=WINDOW_MINWIDTH, height=200)

        # Forward declarations to keep pylint happy
        self.cfg_tree = None
        self.cfg_tree_h_scrollbar = None
        self.cfg_tree_v_scrollbar = None
        self.desc_frame = None
        self.desc_txt = None
        self.pane_divider = None
        self.settings_frame = None
        self.settings_layer_cmb = None
        self.settings_layer_lbl = None
        self.settings_variant_cmb = None
        self.settings_variant_lbl = None

        # Set up control variables
        self.cur_layer = tkinter.StringVar()
        self.last_layer = ""
        self.cur_variant = tkinter.StringVar()
        self.last_variant = ""

        # Divide the window into two panes, which stretch according to the divider's size
        # pane_divider and its frames don't use normal grid layout, so these are setup
        # differently than the other controls.
        self._add_leaf_control(
            "pane_divider",
            tkinter.PanedWindow(
                self.app_root,
                sashwidth=DIVIDER_WIDTH,
                sashrelief=tkinter.SUNKEN
                )
            )
        self.pane_0 = tkinter.ttk.Frame(self.pane_divider, padding=PADDING)
        self.pane_divider.add(self.pane_0)
        self.pane_1 = tkinter.ttk.Frame(self.pane_divider, padding=PADDING)
        self.pane_divider.add(self.pane_1)
        self.pane_divider.paneconfigure(
            self.pane_0,
            padx=PADDING,
            pady=PADDING,
            minsize=PANE_0_MINWIDTH
            )
        self.pane_divider.paneconfigure(
            self.pane_1,
            padx=PADDING,
            pady=PADDING,
            minsize=PANE_1_MINWIDTH
            )

        # Make the cell containing the pane divider autoresize, which in turn allows the
        # panes and their children resize.
        self.app_root.grid_columnconfigure(0, weight=1)
        self.app_root.grid_rowconfigure(0, weight=1)

        # Populate controls
        self.create_menu_bar()
        self.create_pane_0()
        self.create_pane_1()

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
        """"Add a list of menu items to top_menu"""
        for i in cmd_list:
            self.add_menu_item(top_menu, i)

    def create_menu_bar(self):
        """Create the menu bar"""
        M = Util.Container

        top_menu = tkinter.Menu(self.app_root)

        file_menu = tkinter.Menu(top_menu, tearoff=0)
        self.add_menu_items(file_menu, [
            M(t="&Open...", f=self.on_menu_file_open),
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
        self.pane_0.grid_rowconfigure(0, weight=1)

        self._add_leaf_control(
            "cfg_tree",
            tkinter.ttk.Treeview(
                self.pane_0,
                selectmode='browse',
                show="tree"
                )
            )

        self._add_leaf_control(
            "cfg_tree_h_scrollbar",
            tkinter.ttk.Scrollbar(self.pane_0, orient=tkinter.HORIZONTAL),
            row=1,
            col=0
            )
        self._add_leaf_control(
            "cfg_tree_v_scrollbar",
            tkinter.ttk.Scrollbar(self.pane_0, orient=tkinter.VERTICAL),
            row=0,
            col=1
            )

        # Crosslink scroll bars and tree
        self.cfg_tree_h_scrollbar.config(command=self.cfg_tree.xview)
        self.cfg_tree_v_scrollbar.config(command=self.cfg_tree.yview)
        self.cfg_tree.configure(
            xscrollcommand=self.cfg_tree_h_scrollbar.set,
            yscrollcommand=self.cfg_tree_v_scrollbar.set
            )

        # Bind selection handler to this object
        def bind_cfg_tree_cb(_event=None):
            """Binding method to call the handler"""
            iid = self.cfg_tree.focus()
            sel = self.cfg_tree.item(iid)
            self.on_cfg_tree_click(sel["values"][0], sel["tags"][0])

        self.cfg_tree.bind("<<TreeviewSelect>>", bind_cfg_tree_cb)

    def create_pane_1(self):
        """
            Create the controls on the right side of the window
        """
        # Make all controls expand horizontally with the window
        self.pane_1.grid_columnconfigure(0, weight=1)
        # Rows are configured in each function

        self.create_pane_1_view(0)
        self.create_pane_1_description(1)

    def create_pane_1_view(self, row):
        """
            Create the view controls on the right side of the window
        """
        # The view controls do not expand vertically with the window
        self.pane_1.grid_rowconfigure(row, weight=0)

        # View area
        self._add_container_control(
            "settings_frame",
            tkinter.ttk.LabelFrame(
                self.pane_1,
                text="Settings View",
                padding=PADDING
                ),
            row=row,
            num_cols=2,
            num_rows=2
            )
        # Do not resize label row
        self.settings_frame.grid_rowconfigure(0, weight=0)

        # Layer controls
        self._add_leaf_control(
            "settings_layer_lbl",
            tkinter.ttk.Label(self.settings_frame, text="Layer"),
            row=0,
            col=0
            )
        self._add_leaf_control(
            "settings_layer_cmb",
            tkinter.ttk.Combobox(
                self.settings_frame,
                textvariable=self.cur_layer,
                height=1,
                ),
            row=1,
            col=0
            )
        self.settings_layer_cmb.state(["readonly"])

        # Bind write handler to this object
        def cur_layer_cb(*args):
            """Binding method to call the handler"""
            self.on_cur_layer_changed(self.cur_layer.get())

        self.cur_layer.trace("w", cur_layer_cb)

        # Variant controls
        self._add_leaf_control(
            "settings_variant_lbl",
            tkinter.ttk.Label(self.settings_frame, text="Variant"),
            row=0,
            col=1
            )
        self._add_leaf_control(
            "settings_variant_cmb",
            tkinter.ttk.Combobox(self.settings_frame, textvariable=self.cur_variant, height=1),
            row=1,
            col=1
            )
        self.settings_variant_cmb.state(["readonly"])

        # Bind write handler to this object
        def cur_variant_cb(*args):
            """Binding method to call the handler"""
            self.on_cur_variant_changed(self.cur_variant.get())

        self.cur_variant.trace("w", cur_variant_cb)

    def create_pane_1_description(self, row):
        """
            Create the description box on the right side of the window
        """
        # Make this row expand with the size of the window
        self.pane_1.grid_rowconfigure(row, weight=1)

        self._add_container_control(
            "desc_frame",
            tkinter.ttk.LabelFrame(
                self.pane_1,
                text="Description",
                padding=PADDING
                ),
            row=row
            )
        self._add_leaf_control(
            "desc_txt",
            tkinter.Text(
                self.desc_frame,
                font="TkFixedFont",
                relief=tkinter.FLAT,
                background=tkinter.ttk.Style().lookup("TLabelFrame", "background"),
                wrap=tkinter.WORD
                )
            )
        self.set_description("")

    def on_cfg_tree_click(self, value, tag):
        """Handle item clicks"""
        if tag == CFG_TAG.PARAM:
            item = self.param_tbl[value]
            self.set_description(item.param.get_description())
        elif tag == CFG_TAG.MENU:
            self.set_description(value)
        else:
            self.set_description("")

    def on_cur_layer_changed(self, value):
        """Handle changes to the currently selected layer"""
        if self.project is None:
            return

        if value == "":
            return

        v_list = value.split("=")
        v_len = len(v_list)
        if v_len in [1, 2]:
            # Change the <layer>=<variant> form to just <layer>
            layer = v_list[0]
        else:
            print("Error: Invalid layer '{}'".format(value))
            return

        layer = v_list[0]
        self.cur_layer.set(v_list[0])

        if self.last_layer == layer:
            return

        self.last_layer = layer
        variant_names = self.project.get_variant_names(layer)
        self.settings_variant_cmb.configure(values=variant_names)
        self.cur_variant.set(self.settings_view_tbl[layer])

    def on_cur_variant_changed(self, variant):
        """Handle changes to the currently selected variant"""
        if self.project is None:
            return

        if self.last_variant == variant:
            return

        # Update settings table
        self.settings_view_tbl[self.cur_layer.get()] = variant

        # Rebuild layer list options to reflect change
        layer_names = self.project.get_layer_names()
        value_list = []
        for layer in layer_names:
            value_list.append("{}={}".format(layer, self.settings_view_tbl[layer]))
        self.settings_layer_cmb.configure(values=value_list)

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
        if self.project_file:
            self._open_project()

        self.app_root.mainloop()
        return 0

    def set_description(self, text):
        """Set the text in the description box"""
        self.desc_txt.config(state=tkinter.NORMAL)
        self.desc_txt.delete(1.0, tkinter.END)
        self.desc_txt.insert(tkinter.END, text)
        self.desc_txt.config(state=tkinter.DISABLED)

    def _add_container_control(self, name, control, row=0, col=0, num_rows=1, num_cols=1):
        # Create a control which has at least one child
        self._add_leaf_control(name, control, row, col)
        for i in range(num_cols):
            control.grid_columnconfigure(i, weight=1)
        for i in range(num_rows):
            control.grid_rowconfigure(i, weight=1)

    def _add_leaf_control(self, name, control, row=0, col=0):
        # Create a control which has no children
        setattr(self, name, control)
        control.grid(row=row, column=col, sticky=STICKY_FILL)

    def _clear_gui(self):
        # Delete all items in the config tree
        top_items = self.cfg_tree.get_children()
        if top_items:
            self.cfg_tree.delete(top_items)

        # Clear combo boxes
        self.settings_layer_cmb.configure(values=[])
        self.last_layer = ""
        self.cur_layer.set(self.last_layer)
        self.settings_variant_cmb.configure(values=[])
        self.last_variant = ""
        self.cur_variant.set(self.last_variant)

        # Clear other text fields
        self.set_description("")

    def _open_project(self):
        try:
            project, prj_dir, out_dir = Builder.read_project(self.project_file, self.out_dir)
        except Log.GlobifestException as e:
            tkinter.messagebox.showerror(self.APP_TITLE, str(e))
            return

        def_trees = list()

        for pkg in project.get_packages():
            pkg_file = Builder.get_pkg_file(project, pkg, prj_dir, out_dir)
            if not pkg_file:
                tkinter.messagebox.showerror(
                    self.APP_TITLE,
                    "Unknown file root {}".format(str(pkg.file_root))
                    )
                return
            pkg_root = Builder.get_pkg_root(project, pkg, pkg_file, out_dir)
            if pkg_root is None:
                tkinter.messagebox.showerror(
                    self.APP_TITLE,
                    "Unknown package root {}".format(str(pkg.file_root))
                    )
                return

            manifest = Builder.build_manifest(pkg_file, ManifestParser.ConfigsOnly(), pkg_root)
            pkg_dir = os.path.dirname(pkg_file)
            for cfg in manifest.get_configs():
                cfg.definition = Util.get_abs_path(cfg.definition, pkg_dir)
                def_tree = Builder.build_definition(cfg.definition)
                def_trees.append(def_tree)

        # Aggregate DefTrees into a single list
        forest = DefTree.DefForest()
        for tree in def_trees:
            tree.walk(forest)

        self.project = project

        # Clear GUI elements
        self._clear_gui()

        # Set the window title
        self.app_root.title("{} - {}".format(self.APP_TITLE, self.project.get_name()))

        # Walk the forest to populate the config tree
        forest.walk(
            CfgTreeObserver(self.cfg_tree, self.param_tbl),
            child_sorter=gui_child_sorter,
            param_sorter=gui_param_sorter
            )

        # Set up layer/variant boxes
        self.settings_view_tbl.clear()
        layer_names = project.get_layer_names()
        if layer_names:
            for layer in layer_names:
                variant_names = project.get_variant_names(layer)
                self.settings_view_tbl[layer] = (variant_names[0] if variant_names else "")
            value_list = []
            for layer in layer_names:
                value_list.append("{}={}".format(layer, self.settings_view_tbl[layer]))

            self.settings_layer_cmb.configure(values=value_list)
            self.cur_layer.set(layer_names[0])
            # Variant will propagate via layer change

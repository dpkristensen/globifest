#/usr/bin/env python
"""
    globifest/DefTree.py - globifest Configuration Definition

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

import re

from GlobifestLib import Log, Util

PARAM_TYPE = Util.create_enum(
    "BOOL",
    "STRING",
    "INT",
    "FLOAT"
    )

SCOPE_TRIM_RE = re.compile("^/|/$")


def validate_type(ptype):
    """Returns the ptype validated as a PARAM_TYPE value, or None if invalid"""
    if not isinstance(ptype, str):
        return None

    ucase = ptype.upper()
    if ucase not in PARAM_TYPE.enum_id:
        return None

    return PARAM_TYPE.__dict__.get(ucase)


def validate_value(ptype, value):
    """Return the value validated as ptype, or None if invalid"""
    if value is None:
        return None

    ret = None
    if ptype == PARAM_TYPE.BOOL:
        lvalue = value.lower()
        if lvalue == "false":
            ret = False
        elif lvalue == "true":
            ret = True
    elif ptype == PARAM_TYPE.STRING:
        ret = value
    elif ptype == PARAM_TYPE.INT:
        try:
            ret = int(value)
        except ValueError:
            pass
    elif ptype == PARAM_TYPE.FLOAT:
        try:
            ret = float(value)
        except ValueError:
            pass

    return ret


class Parameter(object):
    """
        Encapsulates a parameter definition

        @note This class does not validate parameter data
    """

    def __init__(self, pid, ptitle, ptype, pdesc="", pdefault=None):
        self.pid = pid
        self.ptitle = ptitle
        self.ptype = ptype
        self.pdesc = pdesc
        self.pdefault = pdefault

    def __str__(self):
        s = list()
        if self.pid:
            s.append("id={}".format(self.pid))
        if self.ptype is not None:
            s.append("type={}".format(PARAM_TYPE.enum_id[self.ptype]))
        if self.ptitle:
            s.append("title={}".format(self.ptitle))
        if self.pdefault:
            s.append("default={}".format(self.pdefault))
        if self.pdesc:
            s.append("desc={}".format(self.pdesc))
        return " ".join(s)

    def get_default_value(self):
        """Returns the default value of the parameter"""
        return self.pdefault

    def get_description(self):
        """Returns the description of the parameter"""
        return self.pdesc

    def get_identifier(self):
        """Returns the identifier of the parameter"""
        return self.pid

    def get_title(self):
        """Returns the title of the parameter"""
        return self.ptitle

    def get_type(self):
        """Returns the PARAM_TYPE"""
        return self.ptype

class PrintObserver(object):
    """This class can be used to print a Scope or DefTree"""

    def __init__(self):
        self.level = 0

    def on_def_begin(self, filename):
        """Handler for the beginning of a DefTree"""
        self._print("File: '{}'".format(filename))

    def on_param(self, param):
        """Handle a parameter"""
        self._print(param)

    def on_scope_begin(self, title, description):
        """Handle the beginning of a scope"""
        self._print("{}:".format(title))
        self.level += 1
        if description is not None:
            self._print("<description>={")
            self.level += 1
            for line in description.split("\n"):
                self._print(line)
            self._print("}")
            self.level -= 1

    def on_scope_end(self):
        """Handle the end of a scope"""
        self.level -= 1

    def _print(self, text):
        print("{}{}".format("  " * self.level, str(text)))

class RelevantParamMatcher(object):
    """This class can be used to get relevant parameters from the tree"""

    def __init__(self, settings):
        self.out = []
        self.settings = settings

    def get_params(self):
        """Return a list of parameters for the relevant settings, along with its value"""
        return self.out

    def on_def_begin(self, _filename):
        """Handler for the beginning of a DefTree"""
        pass

    def on_param(self, param):
        """Handle a parameter"""
        try:
            value = self.settings.get_value(param.get_identifier())
            self.out.append(Util.Container(
                param=param,
                value=value
                ))
        except KeyError:
            Log.E("Undefined value {}".format(param))

    def on_scope_begin(self, _title, _description):
        """Handle the beginning of a scope"""
        pass

    def on_scope_end(self):
        """Handle the end of a scope"""
        pass

class Scope(object):
    """Encapsulates a collection of Parameters and nested sub-Scopes"""

    def __init__(self, scope_name, parent_scope):
        self.children = Util.Container()
        self.description = None
        self.params = list()
        self.parent = parent_scope
        self.scope_name = scope_name

    def add_child_scope(self, scope_name):
        """
            Add a child scope with scope_name, if it does not already exist

            Return the child Scope object
        """
        try:
            scope = self.children[scope_name]
        except KeyError:
            # Not found -- add it
            scope = Scope(scope_name=scope_name, parent_scope=self)
            self.children[scope_name] = scope
        return scope

    def add_param(self, new_param):
        """
            Add a parameter to this scope

            Return a reference to the Parameter (for call chaining)
        """
        self.params.append(new_param)
        return new_param

    def get_children(self):
        """Return a reference to the child Scope container"""
        return self.children

    def get_description(self):
        """Return the description of this Scope"""
        return self.description or ""

    def get_name(self):
        """Returns the name of the scope"""
        return self.scope_name

    def get_params(self):
        """Return a list of parameters in this Scope"""
        return self.params

    def set_description(self, text):
        """Set or append to the description for this Scope"""
        if self.description is None:
            self.description = text
        else:
            self.description += "\n\n" + text

    def walk(self, observer):
        # pylint: disable=W0612
        """Walk the tree and visit each node with the given observer"""
        observer.on_scope_begin(self.scope_name, self.description)
        for name, obj in self.children:
            obj.walk(observer)

        for p in self.params:
            observer.on_param(p)

        observer.on_scope_end()

class DefTree(Scope):
    """Encapsulates a nested tree of Parameters"""

    def __init__(self, filename=""):
        Scope.__init__(self, scope_name="/", parent_scope=None)
        self.filename = filename

    def get_filename(self):
        """Returns the filename of the definition"""
        return self.filename

    def get_relevant_params(self, settings):
        """
            Returns the definitions in this tree which are applicable to settings

            The output is a container with param=Parameter and value=<from settings>
        """
        observer = RelevantParamMatcher(settings)
        self.walk(observer)
        return observer.get_params()

    def get_scope(self, scope_path):
        """
            Get the scope by path

            Path nodes are created if they do not exist.

            Returns the scope pertaining to scope_path, or None on invalid path or error.
        """
        # Strip out leading and trailing slashes, as they are optional
        path = SCOPE_TRIM_RE.sub("", scope_path)
        if path:
            nodes = path.split("/")
        else:
            nodes = []

        scope = self
        for node_name in nodes:
            scope = scope.add_child_scope(node_name)
        return scope

    def walk(self, observer):
        """Walk the tree and visit each node with the given observer"""
        observer.on_def_begin(self.filename)
        Scope.walk(self, observer)

new = DefTree

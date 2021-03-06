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
    "FLOAT",
    "ENUM"
    )

SCOPE_TRIM_RE = re.compile("^/|/$")


def no_sort(items):
    """Stub for Scope.walk() method without any sorting"""
    return items


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
    elif ptype == PARAM_TYPE.ENUM:
        ret = value

    return ret


class Parameter(object):
    """
        Encapsulates a parameter definition

        @note This class does not validate parameter data
    """

    def __init__(self, pid, ptitle, ptype, pdesc="", pdefault=None, metadata=None):
        self.pid = pid
        self.ptitle = ptitle
        self.ptype = ptype
        self.pdesc = pdesc
        self.pdefault = pdefault
        self.metadata = metadata

        if (self.ptype == PARAM_TYPE.ENUM) and (not self.metadata):
            Log.E("ENUM must have metadata")

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

        if self.ptype == PARAM_TYPE.ENUM:
            count = self.metadata.get("count", None)
            if count:
                s.append("count={}".format(count))
            vlist = self.metadata.get("vlist", [])
            for v in vlist:
                s.append("choice={},{}".format(v.id, v.text))

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

    def get_implicit_values(self):
        """Gets values implicitly defined by the parameter"""
        out = []
        if self.ptype == PARAM_TYPE.ENUM:
            # Enumerate choices
            counter = 0
            for choice in self.metadata.vlist:
                out.append((choice.id, str(counter)))
                counter += 1

            # Set count, if requested
            count_id = self.metadata.get("count", None)
            if count_id:
                out.append((count_id, str(counter)))

        return out

    def get_implicit_value_by_id(self, pid):
        """Returns an implicit value entry by identifier"""
        if self.ptype == PARAM_TYPE.ENUM:
            for choice in self.metadata.vlist:
                if choice.id == pid:
                    return choice

        return None


    def get_title(self):
        """Returns the title of the parameter"""
        return self.ptitle

    def get_type(self):
        """Returns the PARAM_TYPE"""
        return self.ptype

    def get_text(self):
        """Returns the title if present, or the identifier otherwise"""
        return self.ptitle or self.pid

    def get_metadata(self):
        """Returns metadata associated with the parameter, which may be None"""
        return self.metadata

class BaseObserver(object):
    """Base class for walk() observers"""

    def on_def_begin(self, _filename):
        """Handler for the beginning of a DefTree"""
        pass

    def on_param(self, _param):
        """Handle a parameter"""
        pass

    def on_scope_begin(self, _title, _description):
        """Handle the beginning of a scope"""
        pass

    def on_scope_end(self):
        """Handle the end of a scope"""
        pass

class ImplicitValuesObserver(BaseObserver):
    """This class can be used to get implicit settings from the tree"""

    def __init__(self):
        self.out = Util.Container()

    def get_values(self):
        """Return a container of identifier/value pairs"""
        return self.out

    def on_param(self, param):
        """Handle a parameter"""
        self.out.update(param.get_implicit_values())

class PrintObserver(BaseObserver):
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

class RelevantParamMatcher(BaseObserver):
    """This class can be used to get relevant parameters from the tree"""

    def __init__(self, settings):
        self.out = []
        self.settings = settings

    def get_params(self):
        """Return a list of parameters for the relevant settings, along with its value"""
        return self.out

    def on_param(self, param):
        """Handle a parameter"""
        try:
            value = self.settings.get_value(param.get_identifier())
        except KeyError:
            Log.E("Undefined value {}".format(param))
        self.out.append(Util.Container(
            param=param,
            value=value
            ))

class Scope(object):
    """Encapsulates a collection of Parameters and nested sub-Scopes"""

    class ChildNameGetter(object):
        """
            Getter for sorting by child name
        """
        def __call__(self, obj):
            return obj[1].scope_name.lower()

    class ParamTextGetter(object):
        """
            Getter for sorting by parameter text
        """
        def __call__(self, obj):
            return obj.get_text().lower()

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

    def walk(self, observer, child_sorter=no_sort, param_sorter=no_sort):
        # pylint: disable=W0612
        """Walk the tree and visit each node with the given observer"""
        observer.on_scope_begin(self.scope_name, self.description)
        for name, obj in child_sorter(self.children):
            obj.walk(observer, child_sorter=child_sorter, param_sorter=param_sorter)

        for p in param_sorter(self.params):
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

    def get_implicit_values(self):
        """
            Returns values which implicitly defined by parameters in this tree.

            The output is a container of identifier/value pairs
        """
        observer = ImplicitValuesObserver()
        self.walk(observer)
        return observer.get_values()

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

    def walk(self, observer, child_sorter=no_sort, param_sorter=no_sort):
        """Walk the tree and visit each node with the given observer"""
        observer.on_def_begin(self.filename)
        Scope.walk(self, observer, child_sorter=child_sorter, param_sorter=param_sorter)

class DefForest(Scope):
    """
        This class aggregates information from multiple DefTrees via the walk() method
    """

    class ParamTextGetter(object):
        """
            Return a callable object that fetches the parameter title
        """
        def __call__(self, obj):
            return obj.param.get_text().lower()

    def __init__(self):
        Scope.__init__(self, scope_name="/", parent_scope=None)
        self.scope_stack = list()
        self.cur_filename = ""

    def on_def_begin(self, filename):
        """Save the filename associated with the DefTree"""
        self.cur_filename = filename

    def on_param(self, param):
        """Save all the relevant information about a parameter"""
        self.scope_stack[-1].add_param(Util.Container(
            def_file=self.cur_filename,
            param=param
            ))

    def on_scope_begin(self, title, description):
        """Add a scope level"""
        if self.scope_stack:
            new_scope = self.scope_stack[-1].add_child_scope(title)
            new_scope.set_description(description)
            self.scope_stack.append(new_scope)
        else:
            self.scope_stack.append(self)

    def on_scope_end(self):
        """Pop the current scope level"""
        self.scope_stack.pop()

new = DefTree

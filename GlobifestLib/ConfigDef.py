#/usr/bin/env python
"""
    globifest/ConfigDef.py - globifest Configuration Definition

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

from GlobifestLib import Util

PARAM_TYPE = Util.create_enum(
    "BOOL",
    "STRING",
    "NUMERIC"
    )

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

class Scope(object):
    """Encapsulates a collection of Parameters and nested sub-Scopes"""

    def __init__(self, scope_name, parent_scope):
        self.children = Util.Container()
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

    def get_name(self):
        """Returns the name of the scope"""
        return self.scope_name

    def get_params(self):
        """Return a list of parameters in this Scope"""
        return self.params

class ConfigDef(Scope):
    """Encapsulates a nested tree of Parameters"""

    def __init__(self):
        Scope.__init__(self, scope_name="/", parent_scope=None)

new = ConfigDef

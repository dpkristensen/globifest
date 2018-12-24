#/usr/bin/env python
"""
    globifest/Importer.py - globifest Importer

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

actions = Util.Container()

def create_action(name, arg):
    """
        Factory method for action objects
    """
    action_class = actions.get(name, type(None))
    if issubclass(action_class, ActionBase):
        return action_class(arg)

    return None


def register_action(action_class):
    """
        Register an action class

        An external build script could use this to extend the available actions for proprietary
        and non-portable manifests.
    """
    assert issubclass(action_class, ActionBase)
    actions[action_class.ACTION_TYPE] = action_class


### ACTIONS ###

class ActionBase(object):
    """Base class for actions"""

    ACTION_TYPE = "UNDEFINED"

    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return self.ACTION_TYPE

class DestAction(ActionBase):
    """
        Action to specify a destination

        Argument: File/folder
        Chain Inputs: None
        Chain Outputs: Argument
    """

    ACTION_TYPE = "dest"

register_action(DestAction)

class ExtractAction(ActionBase):
    """
        Action to Extract an archive

        Argument: Text to drop from the beginning of all filenames
        Chain Inputs: Input filename
        Chain Outputs: Folder where the archive was extracted to
    """

    ACTION_TYPE = "extract"

register_action(ExtractAction)

class UrlAction(ActionBase):
    """
        Action to download from a URL

        Chain Inputs: Destination filename (optional)
        Chain Outputs: File name the URL was downloaded to
    """

    ACTION_TYPE = "url"

register_action(UrlAction)

### CORE CLASSES ###

class ExternalDependency(object):
    """Encapsulate logic to set up external dependencies"""

    def __init__(self, name, action_list):
        self.name = name
        self.actions = action_list
        self.out_dir = None

    def __str__(self):
        return "{}: {}".format(self.name, ",".join(a.ACTION_TYPE for a in self.actions))

    def get_actions(self):
        """Return the list of ActionBase objects"""
        return self.actions

    def get_name(self):
        """Return the name/identifier of the dependency"""
        return self.name

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

import hashlib
import os
import random
import shutil
import urllib.request
import zipfile

from GlobifestLib import LineReader, Log, Util

actions = Util.Container()

def create_action(name, arg):
    """
        Factory method for action objects
    """
    action_class = actions.get(name, type(None))
    if issubclass(action_class, ActionBase):
        return action_class(arg)

    return None


def extract_zipfile(zip_filename, out_dir, prefix=None, do_test=True):
    """
        Extract an archive using zipfile

        If prefix is provided then only files with the prefix are used, and
        the prefix is removed from the output path
    """
    with zipfile.ZipFile(zip_filename, mode="r") as zip_fh:
        if do_test:
            bad_file = zip_fh.testzip()
            if bad_file:
                Log.E("Corrupt archive at: {}".format(bad_file))
            else:
                Log.D("  Archive tested OK")
        # Check if doing path replacement, if so, normalize paths
        if prefix:
            Log.D("  Using prefix '{}'".format(prefix))
        Log.D("  Extracting to: {}".format(out_dir))
        for file in zip_fh.infolist():
            if prefix:
                if not file.filename.startswith(prefix):
                    continue
                orig_fn = file.filename
                start_idx = len(prefix)
                try:
                    while file.filename[start_idx] in ["/", "\\"]:
                        # This is a directory; fix up for the user so it does not
                        # extract to the root of the host's filesystem.
                        start_idx += 1
                except IndexError:
                    # Just the prefix, possibly with trailing slashes; just skip.
                    continue
                file.filename = file.filename[start_idx:]
                Log.D("    {} => {}".format(orig_fn, file.filename))
            else:
                Log.D("    {}".format(file.filename))
            zip_fh.extract(file, path=out_dir)


def register_action(action_class):
    """
        Register an action class

        An external build script could use this to extend the available actions for proprietary
        and non-portable manifests.
    """
    assert issubclass(action_class, ActionBase)
    actions[action_class.ACTION_TYPE] = action_class


def read_bin(filename, size=4096):
    """Generator to read a binary file, yields data in size chunks"""
    with open(filename, mode="rb") as fh:
        data = True
        while data:
            data = fh.read(size)
            if data:
                yield data

### ACTIONS ###

class ActionBase(object):
    """Base class for actions"""

    ACTION_TYPE = "UNDEFINED"

    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return self.ACTION_TYPE

    def check_input(self, inputs, num_inputs=0):
        """
            Log an error if there is not the specified number of inputs to this action
            (0 for any number of inputs accepted).
        """
        if num_inputs == 0:
            if inputs:
                return
            self._log_input_error("Expected input list; got", inputs)
        else:
            if len(inputs) == num_inputs:
                return
            self._log_input_error("Expected {} input(s); got".format(num_inputs), inputs)

    def check_no_input(self, inputs):
        """Log an error if there is input to this action"""
        if inputs == []:
            return

        self._log_input_error("Unexpected input; dropping", inputs)

    def log_debug(self, text):
        """Log a debug message pertinent to the action"""
        Log.D("  {}: {}".format(self.ACTION_TYPE, text))

    def log_error(self, text):
        """Log an error performing an action"""
        Log.E("  {}: {}".format(self.ACTION_TYPE, text), stackframe=3)

    def log_info(self, text):
        """Log information pertinent to the action"""
        Log.I("  {}: {}".format(self.ACTION_TYPE, text))

    def get_action_folder(self, ext_dep):
        """Return an output directory for this action"""
        action_dir = Util.get_abs_path(self.ACTION_TYPE, ext_dep.out_dir)
        return action_dir

    def get_action_file(self, ext_dep, extension=None):
        """Create and return a single output filename for this action"""
        action_dir = Util.get_abs_path(
            "{}.{}".format(self.ACTION_TYPE, extension),
            ext_dep.out_dir
            )
        return action_dir

    def run(self, _ext_dep, _inputs):
        """
            Override this function in the concrete class

            Return a list of inputs to feed into the next action
        """
        self.log_error("Cannot perform action")
        return []

    def _log_input_error(self, text, inputs):
        try:
            input_str = "{} item(s)".format(len(inputs))
        except TypeError:
            try:
                input_str = str(inputs)
            except EnvironmentError:
                input_str = "unknown object"
        self.log_error("{} {}".format(text, input_str))

class DestAction(ActionBase):
    """
        Action to specify a destination

        Argument: File/folder
        Chain Inputs: None
        Chain Outputs: Argument
    """

    ACTION_TYPE = "dest"

    def run(self, _ext_dep, inputs):
        """Run the action"""
        self.check_no_input(inputs)
        self.log_debug(self.arg)

        # The argument is the destination
        return [self.arg]

register_action(DestAction)

class ExtractAction(ActionBase):
    """
        Action to Extract an archive

        Argument: Text to drop from the beginning of all filenames
        Chain Inputs: Input filename
        Chain Outputs: Folder where the archive was extracted to
    """

    ACTION_TYPE = "extract"

    def run(self, ext_dep, inputs):
        """Run the action"""
        self.check_input(inputs, 1)
        in_file = inputs[0]

        if not os.path.isfile(in_file):
            self.log_error("Cannot find {}".format(in_file))

        out_dir = self.get_action_folder(ext_dep)
        if os.path.isdir(out_dir):
            self.log_info("Removing old {}".format(out_dir))
            # Must rename the directory before deleting, since shutil.rmtree()
            # may not be immediate, but os.rename() is.  This will prevent
            # conflict with the os.makedirs() call below.
            random_num = random.getrandbits(32)
            out_dir_renamed = os.path.join(
                os.path.dirname(out_dir),
                "{:x}_delete_me".format(random_num)
                )
            self.log_debug("Renaming to {}".format(out_dir_renamed))
            os.rename(out_dir, out_dir_renamed)
            self.log_debug("Deleting {}".format(out_dir_renamed))
            shutil.rmtree(out_dir_renamed, ignore_errors=True)

        self.log_debug("(Re)creating {}".format(out_dir))
        os.makedirs(out_dir)

        self.log_info("Extracting {} (at {}) to {}".format(in_file, self.arg, out_dir))
        if self.arg == ".":
            self.arg = None
        extract_zipfile(
            zip_filename=in_file,
            out_dir=out_dir,
            prefix=self.arg,
            do_test=True
            )

        return [out_dir]

register_action(ExtractAction)

class SHA256Action(ActionBase):
    """
        Action to validate the SHA256 of a file

        Chain Inputs: Input filename
        Chain Outputs: Input filename
    """

    ACTION_TYPE = "sha256"

    def run(self, _ext_dep, inputs):
        """Run the action"""
        self.check_input(inputs, 1)
        in_file = inputs[0]

        self.log_info("Verifying {}".format(in_file))
        v = hashlib.sha256()
        for data in read_bin(in_file):
            v.update(data)

        actual = v.hexdigest()
        if actual != self.arg.lower():
            self.log_error("{} failed, got {}".format(in_file, actual))

        return [in_file]

register_action(SHA256Action)

class UrlAction(ActionBase):
    """
        Action to download from a URL

        Chain Inputs: Destination filename (optional)
        Chain Outputs: File name the URL was downloaded to
    """

    ACTION_TYPE = "url"

    def run(self, ext_dep, inputs):
        """Run the action"""
        if inputs == []:
            dest = self.get_action_file(ext_dep, "dep")
        else:
            self.check_input(inputs, 1)
            dest = Util.get_abs_path(inputs[0], ext_dep.out_dir)

        if os.path.isfile(dest):
            # Downloaded file is probably corrupt, delete it
            self.log_info("Deleting old {}".format(dest))
            os.unlink(dest)

        self.log_info("Downloading file from {} as {}".format(self.arg, dest))
        with urllib.request.urlopen(self.arg) as response, open(dest, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        return [dest]

register_action(UrlAction)

### CORE CLASSES ###

class _SetupBeginAction(ActionBase):
    """Private action to begin setup"""

    ACTION_TYPE = "SETUP"

    def run(self, ext_dep, _inputs=None):
        """Verify the cache file contents, if it exists"""
        cache_ok = False
        filename = self.get_action_file(ext_dep, "cache")
        self.log_debug("Checking settings in {}".format(filename))
        with LineReader.OpenFileCM(filename, "rt") as cache_cm:
            if cache_cm:
                self.log_debug("Reading values")
                # Not providing a real target class is OK as long as we don't
                # try to stringize the LineInfo object.
                reader = LineReader.ReadLineInfoIter(cache_cm.get_file(), target="")
                cache_lines = [line_info.get_text() for line_info in reader]
                if cache_lines == self.arg:
                    cache_ok = True
                else:
                    self.log_debug("Expected:")
                    for line in self.arg:
                        self.log_debug("  '{}'".format(line))
                    self.log_debug("Cached:")
                    for line in cache_lines:
                        self.log_debug("  '{}'".format(line))
            else:
                self.log_debug("No valid cache; (re)running actions")

        return cache_ok

class _SetupCompleteAction(ActionBase):
    """Private action to mark setup as complete"""

    ACTION_TYPE = "SETUP"

    def run(self, ext_dep, _inputs=None):
        """Write the cache file contents"""
        filename = self.get_action_file(ext_dep, "cache")
        self.log_debug("Writing settings to {}".format(filename))
        with open(filename, "wt") as fh:
            for line in self.arg:
                fh.write(line + "\n")
        self.log_debug("Complete")

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

    def setup(self, out_dir):
        """Run setup actions for the external dependency"""
        self.out_dir = out_dir

        # Build the contents of the cache file.  This must include enough information to verify
        # the reproducibility of the actions, so it contains all input parameters to the
        # dependency.
        cache_file_contents = [
            "***Delete this file to re-run dependency setup***",
            "name={}".format(self.name),
            "out_dir={}".format(self.out_dir)
            ]
        for a in self.actions:
            cache_file_contents.append("action {} {}".format(a.ACTION_TYPE, a.arg))

        if _SetupBeginAction(cache_file_contents).run(self):
            Log.I("{} up to date".format(self.name))
            return
        else:
            Log.I("Setting up {}".format(self.name))
        inputs = []
        for a in self.actions:
            inputs = a.run(self, inputs)
        _SetupCompleteAction(cache_file_contents).run(self)

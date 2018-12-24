#/usr/bin/env python
"""
    globifest/Project.py - globifest Project

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

from GlobifestLib import Log, Util

ROOT = Util.create_enum(
    "DEPENDENCY",
    "SOURCE"
    )

class Project(object):
    """
        Encapsulates information necessary to build with various configurations.

        The project has one or more layers, and each layer has one or more variants.  Layers are
        configs structured in priority order, with higher priority layers overriding settings
        defined in lower layers.

        Variants are individual options chosen within each layer, so that only one is active at
        any time.

        See project-format.md for further details.
    """

    ROOT = ROOT

    def __init__(self, filename="", err_ctx=Log.ERROR.RUNTIME, err_fatal=False):
        self.layers = list() # This is a list instead of a container to ensure ordering
        self.err_ctx = err_ctx
        self.err_fatal = err_fatal
        self.filename = filename
        self.prj_name = None
        self.packages = []
        self.dependencies = Util.Container()

    def add_dependency(self, dependency):
        """Add a dependency to the project"""
        self.dependencies[dependency.get_name()] = dependency

    def add_layer(self, layer_name):
        """Push a new layer onto the stack"""
        layer_ref = Util.Container(
            name=layer_name,
            variants=list()
            )
        self.layers.append(layer_ref)

    def add_package(self, filename, file_root=ROOT.SOURCE, module_root=ROOT.SOURCE, module_id=None):
        """
            Add a package to the project

            @param filename     Path to the manifest file
            @param file_root    ROOT enum value corresponding to where the manifest is to be found.
            @param module_root  ROOT enum value corresponding to where the manifest's files can
                                be found.
            @param module_id    Name (identifier) of the dependency for ROOT.DEPENDENCY values.
        """
        self.packages.append(Util.Container(
            filename=filename,
            file_root=file_root,
            module_root=module_root,
            module_id=module_id
            ))

    def add_variant(self, layer_name, variant_name, filename):
        """Add a new variant into the layer"""
        layer_ref = self._get_layer_ref(layer_name)
        if layer_ref is not None:
            variant_ref = Util.Container(
                name=variant_name,
                filename=filename,
                config=Util.Container()
                )
            layer_ref.variants.append(variant_ref)

    def get_dependencies(self):
        """Return the set of dependencies"""
        return self.dependencies

    def get_filename(self):
        """Returns the filename where the project is defined"""
        return self.filename

    def get_layer_names(self):
        """Return a list of the names of each layer, from lowest to highest"""
        return [layer.name for layer in self.layers]

    def get_packages(self):
        """Return a list of packages"""
        return self.packages

    def get_name(self):
        """Returns the name of the project"""
        return self.prj_name

    def get_target(self, layer_name, variant_name=None):
        """
            @note If variant_name is None, only the layer will be returned.
            @return The target associated with the given layer and variant, or None if
                not present.
        """
        if variant_name is None:
            return self._get_layer_ref(layer_name)
        else:
            return self._get_variant_ref(layer_name, variant_name)

    def get_variant_names(self, layer_name):
        """Return a list of the names of each variant in a layer"""
        layer_ref = self._get_layer_ref(layer_name)
        if layer_ref is None:
            return []

        return [variant.name for variant in layer_ref.variants]

    def log_error(self, msg):
        """
            Log an error

            @note The error may not be fatal, so it should be handled as well.
        """
        Log.E(msg, err_type=self.err_ctx, is_fatal=self.err_fatal)

    def set_name(self, name):
        """Sets the name of the project (can only be done once)"""
        if name is None:
            self.log_error("Project name cannot be None")
        elif self.prj_name is None:
            self.prj_name = name
        else:
            self.log_error(
                "Cannot set project name twice. cur={} new={}".format(self.prj_name, name)
                )

    def _get_layer_ref(self, layer_name):
        """@return reference to the layer, or None if not found"""
        for layer in self.layers:
            if layer.name == layer_name:
                return layer

        self.log_error("Attempted to access non-existent layer {}".format(layer_name))
        return None

    def _get_variant_ref(self, layer_name, variant_name):
        """@return reference to the variant, or None if not found"""
        layer_ref = self._get_layer_ref(layer_name)
        if layer_ref is None:
            return None

        for variant in layer_ref.variants:
            if variant.name == variant_name:
                return variant

        self.log_error("Attempted to access non-existent variant {}".format(variant_name))
        return None

new = Project

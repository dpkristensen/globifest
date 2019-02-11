#/usr/bin/env python
"""
    waf/globitool.py - globifest waf tool

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

import copy
import os
import sys

from waflib import Configure, Logs, Errors

PARAMS = [
    "target",
    "project",
    "config",
    "tgt_params",
    "lnk_params",
    "use"
]

class Globitool():
    """Encapsulates logic to build targets from Globifest"""

    # pylint: disable=E1101

    GlobifestLib = None

    def __init__(self, bld, kwargs):
        self.bld = bld
        self.kwargs = kwargs
        self.taskgens = []
        self.pub_includes = []
        self.pub_defines = []

        # Copy required parameters
        for arg in PARAMS:
            self.__setattr__(arg, kwargs[arg])

        # Dynamically import GlobifestLib on first usage
        if Globitool.GlobifestLib is None:
            # Since this file is in the globifest repository, we can always infer its location
            globifest_waf_dir = os.path.dirname(__file__)
            globifest_dir = os.path.dirname(globifest_waf_dir)
            module_path = os.path.abspath(globifest_dir)

            Logs.info("globitool: Using globifest at {}".format(module_path))
            sys.path.append(module_path)
            Globitool.GlobifestLib = __import__('GlobifestLib')
            __import__('GlobifestLib', fromlist="*")

    def run(self):
        """Build the project configuration and add taskgens"""
        Globitool.GlobifestLib.Log.Logger.set_level(Logs.verbose)

        # Set up callbacks for Builder
        callbacks = Globitool.GlobifestLib.Util.Container(
            prebuild=Globitool._callback_prebuild,
            generator=Globitool._callback_generator,
            postprocess=Globitool._callback_postprocess,
            target=Globitool._callback_target,
            postbuild=Globitool._callback_postbuild,
            arg=self
            )

        try:
            outnode = self.bld.bldnode.make_node("globifest")
            Globitool.GlobifestLib.Builder.build_project(
                in_fname=self.project,
                out_dir=outnode.abspath(),
                settings=self.config,
                callbacks=callbacks
                )
        except Globitool.GlobifestLib.Log.GlobifestException as e:
            raise Errors.WafError(
                msg="[{}] {}".format(str(e.get_type()), str(e)),
                ex=e
                )

    def _callback_prebuild(self, metadata):
        """
            Callback prior to iterating over packages

            Preconditions guaranteed by Builder:
            1. Metadata contains:
            * prj_dir - Absolute path to project file
            * out_dir - Absolute path to output directory
            * settings - Merged (effective) settings for the project
            2. Output directory exists
        """
        self._debug([
            "PREBUILD",
            "prj={}".format(metadata.prj_dir),
            "out={}".format(metadata.out_dir)
            ])

    def _callback_generator(self, metadata, defs, generator):
        """
            Callback for running a generator

            Preconditions guaranteed by Builder:
            1. Metadata contains:
            * prj_dir - Absolute path to project file
            * out_dir - Absolute path to output directory
            * settings - Merged (effective) settings for the project
            2. Output directory exists
        """
        gen_file = generator.get_filename()
        formatter = generator.get_formatter()

        debug_msg_list = [
            "GENERATOR",
            "format={}".format(generator.FORMAT_TYPE),
            "file={}".format(gen_file)
            ]
        if formatter:
            debug_msg_list.append("formatter={}".format(formatter))
        self._debug(debug_msg_list)

        # Generating files should hopefully be quick, no perceived need to create a
        # taskgen.
        os.makedirs(os.path.dirname(gen_file), exist_ok=True)
        try:
            generator.generate(defs, metadata.out_dir)
        except EnvironmentError as e:
            raise Errors.WafError("Failed to generate {}".format(gen_file), e)

    def _callback_postprocess(self, metadata):
        """
            Callback after processing manifests

            Preconditions guaranteed by Builder:
            1. The prebuild step has been run
            2. Packages have been parsed
            3. Metadata now also contains
            * pub_includes - Include directories accessible to all packages
            * pub_defines - Definitions accessible to all packages
        """
        self.pub_includes = self._paths_from_node(metadata.pub_includes, self.bld.srcnode)
        self.pub_defines = metadata.pub_defines

        self._debug([
            "POSTPROCESS",
            "pub_includes={}".format(self.pub_includes),
            "pub_defines={}".format(self.pub_defines)
            ])

    def _callback_target(self, metadata, name, tables):
        """
            Callback when a target is processed

            Preconditions guaranteed by Builder:
            1. The postprocess step has been run
            2. Package name is the base file name relative to the project file.
            3. tables contains data specific to this target:
            * prv_includes - Include directories accessible to files in this package
            * prv_defines - Definitions accessible to files in this package
            * sources - Source files for this package
            * aux_files - Auxiliary files associated with this package
        """
        prv_sources = self._paths_from_node(tables.sources, self.bld.srcnode)
        prv_includes = self._paths_from_node(tables.prv_includes, self.bld.srcnode)

        # Convert the name into a path relative to the source node
        name = Globitool.GlobifestLib.Util.get_abs_path(name, metadata.prj_dir)
        name = self._paths_from_node(name, self.bld.srcnode)
        # Then remove all escapes
        name = "_".join(os.path.normpath(name).split(os.sep))

        self._debug([
            "TARGET",
            "package={}".format(name),
            "prv_includes={}".format(prv_includes),
            "prv_defines={}".format(tables.prv_defines),
            "sources={}".format(prv_sources)
            # Aux files are not part of the build system, so not used
            ])

        tgt_name = "_GFT_{}_{}".format(self.target, name)

        # Add a taskgen for this target, copying the target params
        params = copy.copy(self.tgt_params)
        params["target"] = tgt_name
        params["source"] = prv_sources
        params["includes"] = prv_includes + self.pub_includes
        params["export_includes"] = self.pub_includes
        if "defines" not in params:
            params["defines"] = []
        if "use" not in params:
            params["use"] = ""
        if hasattr(self, "use"):
            params["use"] += " " + self.use
        params["defines"] += tables.prv_defines + self.pub_defines
        Logs.info("globitool: Target taskgen {}".format(tgt_name))
        Logs.debug("globitool: {}".format(params))
        tg = self.bld(**params)
        self.taskgens.append(tg)

    def _callback_postbuild(self, _metadata):
        """
            Callback when the builder has completed processing a project
        """
        self._debug(["POSTBUILD"])

        if self.lnk_params:
            # Add a taskgen for linking, copying the target params
            params = copy.copy(self.lnk_params)
            params["target"] = self.target
            if "use" not in params:
                params["use"] = ""
            for tg in self.taskgens:
                params["use"] += " {}".format(tg.get_name())
            if hasattr(self, "use"):
                params["use"] += " " + self.use
            Logs.info("globitool: Link taskgen {}".format(self.target))
            Logs.debug("globitool: {}".format(params))
            tg = self.bld(**params)
            self.taskgens.append(tg)
        else:
            # Create a stub TaskGen with the specified name to provide the public interface and
            # outputs from all targets
            params = copy.copy(self.tgt_params)
            params["target"] = self.target
            if "use" not in params:
                params["use"] = ""
            for tg in self.taskgens:
                params["use"] += " {}".format(tg.get_name())
            if hasattr(self, "use"):
                params["use"] += " " + self.use
            Logs.info("globitool: Aggregate taskgen {}".format(self.target))
            Logs.debug("globitool: {}".format(params))
            self.taskgens.append(self.bld(**params))

    def _debug(self, msg_list):
        header = "globitool: [{}] ".format(self.target)
        out_msg = ""
        for msg in msg_list:
            out_msg += header + msg
            header = " "
        Logs.debug(out_msg)

    def _paths_from_node(self, path, node):
        """Return path(s) converted into paths relative to the given waflib.Node"""
        node_path = node.abspath()
        if isinstance(path, str):
            return os.path.relpath(path, node_path)
        elif isinstance(path, list):
            return [os.path.relpath(p, node_path) for p in path]
        else:
            raise TypeError()

@Configure.conf
def GLOBITOOL(self, **kwargs):
    """
        Add TaskGens for a project using Globifest

        Parameters:
        * project - File name of project file to use
        * config - String or list of strings containing layer=variant configuration
            (can be omitted if the project does not have customizable layering)
        * tgt_params - dict containing the keywords to use for the taskgens created by
            this project.
        * lnk_params - If present, a final link step is performed on these sources; this
            dict contains the keywords to assign to the link taskgen.
        * use - If present, this is applied to all taskgens created by this tool.

        The target names of the intermediate taskgens are auto-generated; a final taskgen
        will be created which exports information from all of the others via "use".

        Returns a list of all taskgens created
    """
    # Set optional parameter defaults
    kwargs["config"] = kwargs.get("config", "")
    kwargs["lnk_params"] = kwargs.get("lnk_params", dict())
    kwargs["use"] = kwargs.get("use", "")

    # Convert list config to a string
    if isinstance(kwargs["config"], list):
        kwargs["config"] = " ".join(kwargs["config"])

    target = kwargs.get("target", "<unknown>")

    for p in PARAMS:
        if p not in kwargs:
            raise Errors.WafError(
                "globitool: Builder for '{}' missing {}".format(target, p)
                )

    tool = Globitool(self, kwargs)
    tool.run()
    return tool.taskgens

#/usr/bin/env python
"""
    globifest/Builder.py - globifest Builders

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
import re

from GlobifestLib import \
    Config, \
    ConfigParser, \
    DefTree, \
    DefinitionParser, \
    LineReader, \
    Log, \
    Manifest, \
    ManifestParser, \
    Matcher, \
    Project, \
    ProjectParser, \
    Settings, \
    Util

def build_config(in_fname):
    """
      Build a config
    """
    config = Config.new(in_fname)
    parser = ConfigParser.new(config)
    reader = LineReader.new(parser)

    reader.read_file_by_name(in_fname)
    return config

def build_definition(in_fname):
    """
      Build a definition
    """
    def_tree = DefTree.new(in_fname)
    parser = DefinitionParser.new(def_tree)
    reader = LineReader.new(parser)

    reader.read_file_by_name(in_fname)
    return def_tree

def build_manifest(in_fname, settings, pkg_root):
    """
      Build a manifest with the given settings
    """
    manifest = Manifest.new(in_fname, pkg_root)
    parser = ManifestParser.new(manifest, settings)
    reader = LineReader.new(parser)

    reader.read_file_by_name(in_fname)
    return manifest

def build_project(in_fname, out_dir, settings, callbacks=Util.Container()):
    """
      Build a project with the given settings
    """
    project = Project.new(in_fname, err_fatal=True)
    parser = ProjectParser.new(project)
    reader = LineReader.new(parser)

    reader.read_file_by_name(in_fname)

    Log.I("Project: {}".format(project.get_name()))
    cwd = os.getcwd()

    prj_dir = Util.get_abs_path(os.path.dirname(project.get_filename()), cwd)
    Log.I("PrjDir: {}".format(prj_dir))

    out_dir = Util.get_abs_path(out_dir, cwd)
    Log.I("OutDir: {}".format(out_dir))

    os.makedirs(out_dir, exist_ok=True)

    # Check external project dependencies
    for dep_name, dependency in project.get_dependencies():
        Log.I("Checking dependency {}...".format(dep_name))
        dep_out_dir = os.path.join(out_dir, dep_name)
        os.makedirs(dep_out_dir, exist_ok=True)
        dependency.setup(dep_out_dir)

    # Set up build configuration
    Log.I("Build configuration:")
    setting_re = re.compile("([^=]+)=(.+)")
    cfg_container = Util.Container() # Unordered, for tracking purposes
    for cfg_entry in settings:
        m = Matcher.new(cfg_entry)
        if not m.is_fullmatch(setting_re):
            Log.E("Malformed setting: {}".format(cfg_entry))
        if cfg_container.get(m[1]):
            Log.E("Conflicting/Duplicate setting: {}".format(cfg_entry))
        Log.I("  {}: {}".format(m[1], m[2]))
        variant = project.get_target(m[1], m[2])
        # Update the filename with the absolute path
        variant.filename = Util.get_abs_path(variant.filename, prj_dir)
        cfg_container[m[1]] = variant

    # Validate that all layers are specified
    for layer in project.get_layer_names():
        variant = cfg_container.get(layer)
        if variant is None:
            variant_names = project.get_variant_names(layer)
            if len(variant_names) == 1:
                # None specified, but there is only one
                variant = project.get_target(layer, variant_names[0])
                Log.D("  **Default selected for layer {}**".format(layer))
                Log.I("  {}: {}".format(layer, variant.name))
                variant.filename = Util.get_abs_path(variant.filename, prj_dir)
                cfg_container[layer] = variant
            else:
                Log.E("Must specify variant for layer {}".format(layer))

    Log.I("Generating settings in layer order:")
    effective_settings = Settings.new()
    for layer in project.get_layer_names():
        variant = cfg_container.get(layer)
        Log.I("  {}: {}".format(layer, variant.filename))
        layer_config = build_config(variant.filename)
        effective_settings.extend(layer_config.get_settings())

    # Generate a metadata object to communicate information back to the caller
    metadata = Util.Container(
        prj_dir=prj_dir,
        out_dir=out_dir,
        settings=effective_settings
    )

    #### PREBUILD CALLBACK ####
    if callbacks.get("prebuild"):
        callbacks.prebuild(callbacks.get("arg"), metadata)

    # Prepare storage for package processing
    for pub_key in ManifestParser.PUBLIC_LABELS:
        metadata[pub_key] = []
    all_manifests = []

    Log.I("Processing packages...")
    for pkg in project.get_packages():
        # Determine package file location
        if pkg.file_root == project.ROOT.SOURCE:
            # File is relative to the project directory
            pkg_file = Util.get_abs_path(pkg.filename, prj_dir)
        elif pkg.file_root == project.ROOT.DEPENDENCY:
            # File is relative to the dependency's output directory
            # (external manifest)
            pkg_file = Util.get_abs_path(
                pkg.filename,
                os.path.join(out_dir, pkg.module_id)
                )
        else:
            Log.I("Unknown file root {}".format(str(pkg.file_root)))
        # Determine package processing root
        if pkg.module_root == project.ROOT.SOURCE:
            # File is relative to the package folder
            pkg_root = os.path.dirname(pkg_file)
        elif pkg.module_root == project.ROOT.DEPENDENCY:
            # File is relative to the dependency's output directory
            # (local manifest)
            pkg_root = os.path.join(out_dir, pkg.module_id)
        else:
            Log.I("Unknown package root {}".format(str(pkg.file_root)))
        Log.I("  {}".format(pkg_file))
        manifest = build_manifest(pkg_file, effective_settings, pkg_root)
        all_manifests.append(manifest)
        pkg_dir = os.path.dirname(pkg_file)
        manifest_out = manifest.get_output()
        # Replace all file paths with absolute paths
        for k in ManifestParser.FILE_LABELS:
            manifest_out[k] = [Util.get_abs_path(x, pkg_dir) for x in manifest_out[k]]
        # Aggregate all public labels
        for pub_key in ManifestParser.PUBLIC_LABELS:
            metadata[pub_key] += manifest_out[pub_key]
        # Dump all the files on extreme mode
        if Log.Logger.has_level(Log.LEVEL.EXTREME):
            for k, v in manifest_out:
                Log.X("    {}:".format(k))
                for f in v:
                    Log.X("      {}".format(f))
        for cfg in manifest.get_configs():
            cfg.definition = Util.get_abs_path(cfg.definition, pkg_dir)
            Log.I("    Parsing {}".format(cfg.definition))
            def_tree = build_definition(cfg.definition)
            defs = def_tree.get_relevant_params(effective_settings)
            for gen in cfg.generators:
                gen_file = Util.get_abs_path(gen.get_filename(), pkg_dir)
                gen_file = os.path.relpath(gen_file, start=pkg_dir)
                gen_file = os.path.normpath(gen_file)
                gen_file = os.path.join(out_dir, gen_file)
                # Update the filename in the generator
                gen.filename = gen_file
                Log.I("      Generating {}".format(gen_file))
                if gen.get_formatter():
                    formatter_filename = Util.get_abs_path(gen.get_formatter(), pkg_dir)
                    Log.I("      Executing {}".format(formatter_filename))
                #### GENERATOR CALLBACK ####
                if callbacks.get("generator"):
                    # Let the build script intercept the generator without any filesystem changes
                    callbacks.generator(callbacks.get("arg", None), metadata, defs)
                else:
                    os.makedirs(os.path.dirname(gen_file), exist_ok=True)
                    gen.generate(defs, out_dir)

    #### POSTPROCESS CALLBACK ####
    if callbacks.get("postprocess"):
        callbacks.postprocess(callbacks.get("arg"), metadata)

    # Add public data into each manifest and build
    if callbacks.get("target"):
        for manifest in all_manifests:
            tables = Util.Container()
            manifest_out = manifest.get_output()
            for k, v in manifest_out:
                if not k in ManifestParser.PUBLIC_LABELS:
                    tables[k] = v
            manifest_name = os.path.relpath(manifest.get_filename(), start=prj_dir)
            manifest_name = os.path.normpath(manifest_name)
            manifest_name = os.path.splitext(manifest_name)[0]

            #### BUILD TARGET CALLBACK ####
            callbacks.target(callbacks.get("arg", None), metadata, manifest_name, tables)

    #### POSTBUILD CALLBACK ####
    if callbacks.get("postbuild"):
        callbacks.postbuild(callbacks.get("arg", None), metadata)

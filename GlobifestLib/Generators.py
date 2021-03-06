#/usr/bin/env python
"""
    globifest/Generators.py - globifest Generators

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
import runpy

from GlobifestLib import DefTree, LineReader, Log, Util

generators = Util.Container()

def register_generator(gen_class):
    """
        Register a generator class

        An external build script could use this to extend the allowable formats for proprietary
        and non-portable manifests.
    """
    generators[gen_class.FORMAT_TYPE] = gen_class

class GeneratorBase(object):
    """Base class for generators"""

    def __init__(self, filename, formatter):
        self.formatter = formatter
        self.filename = filename

    def generate(self, _definitions, _out_dir):
        """Generate a settings file"""
        Log.E("Error generating {}: algorithm undefined", self.filename)

    def get_filename(self):
        """Return the filename"""
        return self.filename

    def get_formatter(self):
        """Returns None (most classes do not use a formatter)"""
        return None

class CGenerator(GeneratorBase):
    """Generates C headers"""

    FORMAT_TYPE = "c"

    INCLUDE_GUARD_REPLACE = re.compile("([^a-zA-Z0-9_])")

    def generate(self, definitions, out_dir):
        """Generate a settings file"""
        include_guard = os.path.relpath(self.filename, start=out_dir)
        include_guard = "_{}".format(CGenerator.INCLUDE_GUARD_REPLACE.sub("_", include_guard))
        include_guard = include_guard.upper()
        with LineReader.OpenFileCM(self.filename, "wt") as hdr_cm:
            if not hdr_cm:
                Log.E("Could not open {}: {}".format(self.filename, hdr_cm.get_err_msg()))

            hdr_file = hdr_cm.get_file()

            # File header
            hdr_file.write("\n".join([
                "/* GENERATED BY GLOBIFEST -- DO NOT EDIT */",
                "",
                "#ifndef {}".format(include_guard),
                "#define {}".format(include_guard),
                "\n"
            ]))

            # Add values; preprocessor directives are used for maximum type flexibility
            for d in definitions:
                ptype = d.param.get_type()
                pid = d.param.get_identifier()
                value = d.value

                # Write implicit values first
                implicit_id = None
                for implicit_value in d.param.get_implicit_values():
                    hdr_file.write("#define {} ({})\n".format(
                        implicit_value[0],
                        implicit_value[1]
                        ))
                    if value == implicit_value[1]:
                        implicit_id = implicit_value[0]

                # Write the parameter
                if ptype in [DefTree.PARAM_TYPE.INT, DefTree.PARAM_TYPE.FLOAT]:
                    # Parentheses prevent conflicts with surrounding code
                    # Default type of INT is int (i.e., signed  literal)
                    # Default type of FLOAT is double precision
                    hdr_file.write("#define {} ({})\n".format(pid, value))
                elif ptype == DefTree.PARAM_TYPE.STRING:
                    # Strings are not surrounded to allow compile-time concatenation
                    hdr_file.write("#define {} {}\n".format(pid, value))
                elif ptype == DefTree.PARAM_TYPE.BOOL:
                    # Define as 1/0, since C89 did not define TRUE and FALSE values
                    if value == "FALSE":
                        value = 0
                    else:
                        value = 1
                    hdr_file.write("#define {} ({})\n".format(pid, value))
                elif ptype == DefTree.PARAM_TYPE.ENUM:
                    if implicit_id:
                        hdr_file.write("#define {} {}\n".format(pid, implicit_id))
                    else:
                        hdr_file.write("#define {} ({})\n".format(pid, value))
                else:
                    # TODO: Handle more complex literal types:
                    # - Integral types U/L/UL/LL/ULL
                    # - Float suffixes F/L for floats
                    Log.E("Unhandled value of type {}".format(str(d.param.ptype)))

            # File footer
            hdr_file.write("\n#endif /* {} */\n".format(include_guard))

register_generator(CGenerator)

class CustomGenerator(GeneratorBase):
    """Generates files using a custom formatter"""

    FORMAT_TYPE = "_custom"

    def generate(self, definitions, out_dir):
        """Generate a settings file"""
        args = dict(
            DEFINITIONS=definitions,
            OUT_DIR=out_dir,
            OUT_FILE=self.filename,
            PARAM_TYPE=DefTree.PARAM_TYPE,
            g_print=lambda msg: Log.I("        {}".format(str(msg))),
            g_debug=lambda msg: Log.D("        {}".format(str(msg))),
            g_err=lambda msg: Log.E(msg, stackframe=3)
            )
        runpy.run_path(self.formatter, init_globals=args, run_name="<globifest>")

    def get_formatter(self):
        """Returns the formatter used"""
        return self.formatter

register_generator(CustomGenerator)

class JavaGenerator(GeneratorBase):
    """Generates Java files"""

    FORMAT_TYPE = "java"
    PACKAGE_RE = re.compile(r"[\\/]")
    CLASS_RE = re.compile(r".java$")

    def generate(self, definitions, out_dir):
        """Generate a settings file"""
        java_file = self.filename.lower()
        package_dir = os.path.dirname(java_file)
        package_name = os.path.relpath(package_dir, start=out_dir)
        package_name = self.PACKAGE_RE.sub(".", package_name)
        class_name = self.CLASS_RE.sub("", os.path.basename(self.filename))
        os.makedirs(Util.get_abs_path(package_dir, out_dir), exist_ok=True)
        with LineReader.OpenFileCM(java_file, "wt") as hdr_cm:
            if not hdr_cm:
                Log.E("Could not open {}: {}".format(self.filename, hdr_cm.get_err_msg()))

            hdr_file = hdr_cm.get_file()

            # File header
            hdr_file.write("\n".join([
                "/* GENERATED BY GLOBIFEST -- DO NOT EDIT */",
                "",
                "package {}".format(package_name),
                "",
                "public final class {}".format(class_name),
                "{\n"
            ]))

            # Add values
            template = "    public final static {} {} = {};\n"
            for d in definitions:
                ptype = d.param.get_type()
                pid = d.param.get_identifier()
                value = d.value

                # Write implicit values first
                implicit_id = None
                for implicit_value in d.param.get_implicit_values():
                    hdr_file.write(template.format(
                        "int",
                        implicit_value[0],
                        implicit_value[1]
                        ))
                    if value == implicit_value[1]:
                        implicit_id = implicit_value[0]

                # Write the parameter
                if ptype == DefTree.PARAM_TYPE.INT:
                    hdr_file.write(template.format("int", pid, value))
                elif ptype == DefTree.PARAM_TYPE.FLOAT:
                    # Default type is double precision
                    hdr_file.write(template.format("double", pid, value))
                elif ptype == DefTree.PARAM_TYPE.STRING:
                    hdr_file.write(template.format("String", pid, value))
                elif ptype == DefTree.PARAM_TYPE.BOOL:
                    hdr_file.write(template.format("boolean", pid, value.lower()))
                elif ptype == DefTree.PARAM_TYPE.ENUM:
                    if implicit_id:
                        value = implicit_id
                    hdr_file.write(template.format("int", pid, value))
                else:
                    # TODO: Handle more complex literal types
                    Log.E("Unhandled value of type {}".format(str(d.param.ptype)))

            # File footer
            hdr_file.write("}\n")

register_generator(JavaGenerator)

def factory(gen_format, filename, formatter=None):
    """Return a generator for the given format, or None if not registerd"""
    gen_class = generators.get(gen_format)
    if gen_class:
        return gen_class(filename, formatter)

    return None

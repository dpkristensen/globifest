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

from GlobifestLib import Log, Util

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

    def generate(self, settings):
        """Generate a settings file"""
        Log.E("Generation undefined")

    def get_filename(self):
        """Return the filename"""
        return self.filename

    def get_formatter(self):
        """Returns None (most classes do not use a formatter)"""
        return None

class CGenerator(GeneratorBase):
    """Generates C headers"""

    FORMAT_TYPE = "c"

    def generate(self, settings):
        """Generate a settings file"""
        Log.E("Not yet implemented")

register_generator(CGenerator)

class CustomGenerator(GeneratorBase):
    """Generates files using a custom formatter"""

    FORMAT_TYPE = "custom"

    def generate(self, settings):
        """Generate a settings file"""
        Log.E("Not yet implemented")

    def get_formatter(self):
        """Returns the formatter used"""
        return self.formatter

register_generator(CustomGenerator)

class JavaGenerator(GeneratorBase):
    """Generates Java files"""

    FORMAT_TYPE = "java"

    def generate(self, settings, filename):
        """Generate a settings file"""
        Log.E("Not yet implemented")

register_generator(JavaGenerator)

def factory(gen_format, filename, formatter):
    """Return a generator for the given format, or None if not registerd"""
    gen_class = generators.get(gen_format.lower())
    if gen_class:
        return gen_class(filename, formatter)

    return None

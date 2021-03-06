#/usr/bin/env python
"""
    globifest/Util.py - globifest Utility Functions

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
import inspect
import os

def create_enum(*identifiers):
    """
    Create an enumeration class from a list of identifiers passed as strings.  Each value
    increments over the previous by 1.

    If not defined, COUNT will be defined as the last identifier.
    """
    values = dict(zip(identifiers, range(len(identifiers))))
    if "COUNT" not in values:
        values["COUNT"] = len(identifiers)

    values["__str__"] = _enum_str
    values["enum_id"] = identifiers

    return type('Enum', (), values)


def create_flag_enum(*identifiers):
    """
    Create an enumeration class from a list of identifiers passed as strings.  Each value
    will be a power of 2.

    If not defined, ALL will be defined as a bitmask setting all bits to 1.
    """
    bits = dict(zip(identifiers, power_of_2(range(len(identifiers)))))
    if "ALL" not in bits:
        bits["ALL"] = (2 ** len(identifiers)) - 1

    bits["__str__"] = _enum_str

    return type('FlagEnum', (), bits)


def get_abs_path(path, base):
    """Convert the path (absolute or relative to base) into a normalized absolute path"""
    new_path = path
    if not os.path.isabs(path):
        new_path = os.path.join(base, path)
    return os.path.normpath(new_path)


def get_line_number(levels=1):
    """
    Get the line number from the specified stack frame
    """
    frame = get_stackframe(levels)
    if not frame:
        return -1
    return frame.f_lineno


def get_stackframe(levels=1):
    """
    Get the specified stack frame
    """
    frame = inspect.currentframe()
    for _i in range(0, levels):
        frame = frame.f_back
    return frame


def power_of_2(in_list):
    """
    Return a list of powers of 2, corresponding to each value from in_list.
    """
    return [2 ** n for n in in_list]


def _enum_str(self):
    print(self.__dict__)
    return ""

class Container(dict):
    """
        dict-like object that provides access to members via x.y

        Also provides the ability to compare against another dict or Container
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def __iter__(self):
        return iter(self.items())

    def __copy__(self):
        new_obj = Container()
        for k, v in self.items():
            new_obj[k] = v
        return new_obj

    def __deepcopy__(self, memo):
        new_obj = Container()
        for k, v in self.items():
            new_obj[k] = copy.deepcopy(v, memo)
        return new_obj

    def __str__(self):
        outstr = ""
        for top_key, top_value in self.items():
            if isinstance(top_value, list):
                outstr += "\n{}:".format(top_key)
                for entry in top_value:
                    outstr += "\n  {}".format(entry)
            else:
                outstr += "{} = {}\n".format(top_key, top_value)

        return outstr

    def get_diff(self, other):
        """
            Return a containerized diff between this and the other container

            @note list elements in the first nesting level are deduplicated, but the algorithm is
                not recursive to deeper list elements.
        """
        # First make a copy of this dict
        out_dict = copy.deepcopy(self)

        # Deduplicate lists lists
        for k, v in other:
            if k not in out_dict:
                # Add any missing top-level element
                out_dict[k] = copy.deepcopy(v)
            elif isinstance(v, list):
                # If the element is a list, create diffs of the two
                o1 = [e for e in out_dict[k] if e not in other[k]]
                o2 = [e for e in other[k] if e not in out_dict[k]]
                out_dict[k] = o1 + o2
                if not out_dict[k]:
                    del out_dict[k]
            elif v != out_dict.get(k):
                out_dict[k + " (A)"] = out_dict[k]
                out_dict[k + " (B)"] = v
                del out_dict[k]
            else:
                # Remove any top-level non-iterable element
                del out_dict[k]

        return Container(out_dict)

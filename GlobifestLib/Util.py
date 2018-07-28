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

def create_enum(*identifiers):
    values = dict(zip(identifiers, range(len(identifiers))))
    if not ("COUNT" in values):
        values["COUNT"] = len(identifiers)

    values["__str__"] = _enum_str

    return type('Enum', (), values)


def create_flag_enum(*identifiers):
    bits = dict(zip(identifiers, power_of_2(range(len(identifiers)))))
    if not ("ALL" in bits):
        bits["ALL"] = (2 ** len(identifiers)) - 1

    bits["__str__"] = _enum_str

    return type('FlagEnum', (), bits)


def get_line_number(levels=1):
    frame = get_stackframe(levels)
    if not frame:
        return -1
    return frame.f_lineno


def get_stackframe(levels=1):
    frame = inspect.currentframe()
    for i in range(0,levels):
        frame = frame.f_back
    return frame


def power_of_2(in_list):
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

    def __deepcopy__(self, memo):
        new_obj = Container()
        for k,v in self.items():
            new_obj[k] = copy.deepcopy(v, memo)
        return new_obj

    def __str__(self):
        outstr = ""
        for top_key,top_value in self.items():
            if isinstance(top_value, list):
                outstr += "\n{}:".format(top_key)
                for entry in top_value:
                    outstr += "\n  {}".format(entry)
            else:
                outstr += "{} = {}\n".format(top_key, top_value)

        return outstr

    def _get_diff(self, other):
        # First make a copy of this dict
        out_dict = copy.deepcopy(self)

        # Add/Remove any element in the 2nd list that does not exist in the first
        for k,v in other:
            if k not in out_dict:
                # Add any missing top-level element
                out_dict[k] = copy.deepcopy(v)
            elif isinstance(v, list):
                o1 = [e for e in out_dict[k] if e not in other[k]]
                o2 = [e for e in other[k] if e not in out_dict[k]]
                out_dict[k] = o1 + o2
                if len(out_dict[k]) == 0:
                    del out_dict[k]
            else:
                # Remove any top-level non-iterable element
                del out_dict[k]

        return Container(out_dict)

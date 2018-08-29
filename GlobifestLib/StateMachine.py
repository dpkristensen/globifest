#/usr/bin/env python
"""
    globifest/StateMachine.py - globifest State Machine

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

class StateMachine(Log.Debuggable):
    """
        Implements shared state machine functionality
    """

    def __init__(self, debug_mode=False):
        """
            Initialize the class
        """
        Log.Debuggable.__init__(self, debug_mode)

        self._sm_base = Util.Container(
            state=0,
            new_state=0
            )
        self.title = "state"

    def _do_state_transition(self):
        if self._sm_base.new_state != self._sm_base.state:
            self._sm_base.state = self._sm_base.new_state
            return True
        else:
            return False

    def _get_state(self):
        return self._sm_base.state

    def _get_new_state(self):
        return self._sm_base.new_state

    def _set_title(self, text):
        self.title = text

    def _set_state(self, new_state):
        if new_state != self._sm_base.state:
            self._debug("{}={}->{}".format(self.title, self._sm_base.state, new_state))
        self._sm_base.new_state = new_state

    def _transition(self, new_state):
        self._set_state(new_state)
        return self._do_state_transition()

Base = StateMachine

def Owned(parent, title):
    """
    Factory method to create an owned state machine, which links to the parent's debug log.
    """
    sm = StateMachine()
    sm.link_debug_log(parent)
    sm._set_title(title)
    return sm

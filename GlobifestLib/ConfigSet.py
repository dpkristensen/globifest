#/usr/bin/env python
"""
    globifest/ConfigSet.py - globifest Configuration set

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

import re

from GlobifestLib import BoundedStatefulParser, Log, Matcher, StatefulParser, Util

class TokenBase(object):
    def get_name(self):
        return str(self.get_value())

    def get_value(self):
        return self.value

    def matches_class(self, base_type):
        return isinstance(self, base_type)

    def matches_type(self, tok):
        return isinstance(self.get_value(), type(tok.get_value()))

class BoolToken(TokenBase):
    TOKEN_TYPE = "bool"

    def __init__(self, value):
        self.value = value

class IntToken(TokenBase):
    TOKEN_TYPE = "int"

    def __init__(self, text):
        try:
            self.value = int(text)
        except ValueError:
            Log.E("{} is not a number".format(text))

class StringToken(TokenBase):
    TOKEN_TYPE = "string"

    def __init__(self, text):
        self.value = text

class IdentToken(TokenBase):
    TOKEN_TYPE = "identifier"
    STRING_CONFIG_RE = re.compile("^\"(.*)\"$")

    def __init__(self, ident, configset):
        self.ident = ident
        if configset.has_value(ident):
            lookup_val = configset.get_value(ident)
            if lookup_val is None:
                Log.E("{} has no value".format(ident))

            # Discover the data type from context
            m = Matcher.new(lookup_val)
            if lookup_val in RESERVED_IDENT_MAP:
                mapped_ident = RESERVED_IDENT_MAP[lookup_val]
                lookup_val = mapped_ident[RESERVED_IDENT.VALUE]
                self.ident_class = mapped_ident[RESERVED_IDENT.CLASS]
            elif m.is_fullmatch(self.STRING_CONFIG_RE):
                lookup_val = m[1]
                self.ident_class = StringToken
            elif lookup_val.isnumeric():
                lookup_val = int(lookup_val)
                self.ident_class = IntToken
            else:
                Log.E("Malformed config value {}".format(lookup_val))
            self.value = lookup_val
        else:
            Log.E("{} not defined".format(ident))

    def get_name(self):
        return self.ident

    def get_value(self):
        return self.value

    def matches_class(self, base_type):
        return issubclass(self.ident_class, base_type)

    def matches_type(self, tok):
        tok_type = tok.TOKEN_TYPE
        if tok_type == IdentToken.TOKEN_TYPE:
            tok_type = tok.ident_class.TOKEN_TYPE

        return self.ident_class.TOKEN_TYPE == tok_type

class OpBase(Log.Debuggable):
    def __init__(self, parent):
        Log.Debuggable.__init__(self)
        self.tokens = list()
        if parent:
            self.link_debug_log(parent)

    def add_token(self, token):
        if not isinstance(token, TokenBase):
            Log.E("{} is not a token".format(str(token)))
        self.tokens.append(token)

    def get_error(self):
        if len(self.tokens) > self.NUM_ARGS:
            return "{} expects {} args, found {}".format(self.OP_TEXT, self.NUM_ARGS, len(self.tokens))

        return None

    def is_full(self):
        return len(self.tokens) == self.NUM_ARGS

class OpUnaryBase(OpBase):
    NUM_ARGS = 1

    def _eval_check_type(self, base_type):
        tok = self.tokens[0]
        if not tok.matches_class(base_type):
            Log.E("{} must be '{}'".format(tok.get_value(), base_type.TOKEN_TYPE))

    def _eval_op(self, base_type):
        tok = self.tokens[0]
        arg = tok.get_value()
        self._eval_check_type(base_type)
        self._debug("OP EVAL: {} {}({})".format(
            self.OP_TEXT,
            tok.get_name(),
            str(arg),
            ))
        self._debug("  EXPR=" + self._eval_get_expr())
        self._debug("  arg={}({})".format(arg, type(arg)))
        result = eval(self._eval_get_expr())
        self._debug("RESULT: {}".format(result))
        return result

class OpBinaryBase(OpBase):
    NUM_ARGS = 2
    WORKS_WITH_STRING = False

    def evaluate(self):
        return self._eval_op()

    def _eval_check_types(self):
        tok1 = self.tokens[0]
        tok2 = self.tokens[1]
        if not tok1.matches_type(tok2):
            Log.E("Type mismatch: {}({}) {} {}({})".format(
                tok1.get_name(),
                tok1.TOKEN_TYPE,
                self.OP_TEXT,
                tok2.get_name(),
                tok2.TOKEN_TYPE
                ))

        # Strings (not Ident with string values) have restrictions on which operators can be used.
        is_string_tok = (tok1.matches_class(StringToken)) or (tok2.matches_class(StringToken))
        if is_string_tok and not self.WORKS_WITH_STRING:
            Log.E("Type '{}' cannot be used with operator '{}'".format(
                tok1.TOKEN_TYPE,
                self.OP_TEXT
                ))

    def _eval_get_expr(self):
        return "arg1 {} arg2".format(self.OP_TEXT)

    def _eval_op(self):
        tok1 = self.tokens[0]
        tok2 = self.tokens[1]

        arg1 = tok1.get_value()
        arg2 = tok2.get_value()

        self._eval_check_types()
        self._debug("OP EVAL: {}({}) {} {}({})".format(
            tok1.get_name(),
            str(arg1),
            self.OP_TEXT,
            tok2.get_name(),
            str(arg2)
            ))
        self._debug("  EXPR=" + self._eval_get_expr())
        self._debug("  arg1={}({})".format(arg1, type(arg1)))
        self._debug("  arg2={}({})".format(arg2, type(arg2)))
        self._debug("  ACTUAL EXPR={}".format(self._eval_get_expr()))
        result = eval(self._eval_get_expr())
        self._debug("RESULT: {}".format(result))
        return result

class OpInverse(OpUnaryBase):
    OP_TEXT = "!"

    def _eval_get_expr(self):
        return "not arg"

    def evaluate(self):
        return self._eval_op(BoolToken)

class OpCompareBase(OpBinaryBase):
    pass

class OpCompareEq(OpCompareBase):
    OP_TEXT = "=="
    WORKS_WITH_STRING = True

class OpCompareNe(OpCompareBase):
    OP_TEXT = "!="
    WORKS_WITH_STRING = True

class OpCompareLt(OpCompareBase):
    OP_TEXT = "<"

class OpCompareLe(OpCompareBase):
    OP_TEXT = "<="

class OpCompareGt(OpCompareBase):
    OP_TEXT = ">"

class OpCompareGe(OpCompareBase):
    OP_TEXT = ">="

class OpLogicalBase(OpBinaryBase):
    def _eval_check_types(self):
        for t in self.tokens:
            if not t.matches_class(BoolToken):
                Log.E("{} is not a boolean value".format(t.get_value()))

    def _eval_get_expr(self):
        return "arg1 {} arg2".format(self.LOGICAL_OP)

class OpLogicalAnd(OpLogicalBase):
    OP_TEXT = "&&"
    LOGICAL_OP = "and"

class OpLogicalOr(OpLogicalBase):
    OP_TEXT = "||"
    LOGICAL_OP = "or"

RESERVED_IDENT = Util.create_enum(
    "VALUE",
    "CLASS",

    "COUNT"
    )

RESERVED_IDENT_MAP = Util.Container(
    TRUE = (True, BoolToken),
    FALSE = (False, BoolToken)
)

assert(RESERVED_IDENT.COUNT == len(RESERVED_IDENT_MAP))

class ConfigSet(Log.Debuggable):
    """
        Encapsulates a set of configuration values
    """

    def __init__(self, configs, debug_mode=False):
        Log.Debuggable.__init__(self, debug_mode)
        self.configs = configs

        for k,v in configs:
            if k in RESERVED_IDENT_MAP:
                self.Logs.E("Identifier {} is reserved".format(k))

        self.ident_re = re.compile("^([a-zA-Z_0-9]+)(.*)")
        self.string_re = re.compile("^([a-zA-Z_0-9]+)(.*)")
        self.int_re = re.compile("^([0-9\-]+)(.*)")
        self.op_re = re.compile("^(!=|==|=|!|<=|<|>=|>|&&|\|\|)(.*)")
        self.whitespace_re = re.compile("^\s+(.*)")

    def __str__(self):
        outstr = "Configs:\n" + str(self.configs)
        return outstr

    def get_value(self, name):
        return self.configs[name]

    def has_value(self, name):
        return name in self.configs

    def evaluate(self, expr):
        self.expr = expr

        BOUNDED_PARSER_FLAGS = 0
        if self.get_debug_mode():
            BOUNDED_PARSER_FLAGS |= StatefulParser.FLAGS.DEBUG

        op = None
        tok = None
        while True:
            # Fill up the operation
            if op:
                if tok:
                    op.add_token(tok)
                    tok = None
                err_text = op.get_error()
                if err_text:
                    Log.E(err_text)

                if op.is_full():
                    # Evaluate and use the result as the next token
                    tok = BoolToken(op.evaluate())
                    op = None
                    continue
            if self.expr == "":
                if op:
                    Log.E("Operator '{}' missing argument".format(op.OP_TEXT))
                break

            # Identify the next token
            m = Matcher.new(self.expr)

            if m.is_fullmatch(self.whitespace_re):
                self.expr = m[1]
                continue

            if m.is_fullmatch(self.int_re):
                self._debug("INT: " + m[1])
                if tok:
                    Log.E("Unexpected integer '{}'".format(m[1]))
                tok = IntToken(m[1])
                self.expr = m[2]
                continue

            if m.is_fullmatch(self.ident_re):
                if tok:
                    Log.E("Unexpected identifier '{}'".format(m[1]))
                ident = m[1]
                if ident in RESERVED_IDENT_MAP:
                    mapped_ident = RESERVED_IDENT_MAP[ident]
                    mapped_class = mapped_ident[RESERVED_IDENT.CLASS]
                    mapped_value = mapped_ident[RESERVED_IDENT.VALUE]
                    self._debug("RESERVED: {} class={}".format(
                        ident,
                        mapped_class.TOKEN_TYPE,
                        mapped_value
                        ))
                    tok = mapped_class(mapped_value)
                else:
                    self._debug("IDENT: " + ident)
                    tok = IdentToken(m[1], self)
                self.expr = m[2]
                continue

            if m.is_fullmatch(self.op_re):
                self._debug("OP: " + m[1])
                if op != None:
                    Log.E("Spurious operator '{}' after operator '{}'".format(m[1], op.OP_TEXT))
                if m[1] == "!":
                    if tok:
                        Log.E("Unexpected operator '{}'".format(m[1]))
                    op = OpInverse(self)
                elif not tok:
                    Log.E("Operator '{}' missing value".format(m[1]))
                elif (m[1] == "==") or (m[1] == "="):
                    op = OpCompareEq(self)
                elif m[1] == "!=":
                    op = OpCompareNe(self)
                elif m[1] == "<":
                    op = OpCompareLt(self)
                elif m[1] == "<=":
                    op = OpCompareLe(self)
                elif m[1] == ">":
                    op = OpCompareGt(self)
                elif m[1] == ">=":
                    op = OpCompareGe(self)
                elif m[1] == "&&":
                    op = OpLogicalAnd(self)
                elif m[1] == "||":
                    op = OpLogicalOr(self)
                else:
                    Log.E("Unknown operator {}".format(m[1]))

                self.expr = m[2]
                continue

            if self.expr[0] == "(":
                string_parser = BoundedStatefulParser.new(
                    self.expr,
                    "(", ")",
                    BOUNDED_PARSER_FLAGS | StatefulParser.FLAGS.MULTI_LEVEL
                    )
                self._debug("PAREN: " + string_parser.get_parsed_text())
                if StatefulParser.PARSE_STATUS.FINISHED != string_parser.get_status():
                    self._debug(string_parser.get_debug_log())
                    Log.E("Malformed parenthetical in expression: " + self.expr)
                tok = BoolToken(self.evaluate(string_parser.get_parsed_text()))
                self.expr = string_parser.get_remaining_text()
                continue

            if self.expr[0] == "\"":
                string_parser = BoundedStatefulParser.new(self.expr, "\"", flags=BOUNDED_PARSER_FLAGS)
                if StatefulParser.PARSE_STATUS.FINISHED != string_parser.get_status():
                    Log.E("Malformed string in expression: " + self.expr)
                self._debug("STRING DQ: " + string_parser.get_parsed_text())
                tok = StringToken(string_parser.get_parsed_text())
                self.expr = string_parser.get_remaining_text()
                continue

            if self.expr[0] == "'":
                string_parser = BoundedStatefulParser.new(self.expr, "'", flags=BOUNDED_PARSER_FLAGS)
                if StatefulParser.PARSE_STATUS.FINISHED != string_parser.get_status():
                    Log.E("Malformed string in expression: " + self.expr)
                self._debug("STRING SQ: " + string_parser.get_parsed_text())
                tok = StringToken(string_parser.get_parsed_text())
                self.expr = string_parser.get_remaining_text()
                continue

            Log.E("Bad expression: " + self.expr)

        if tok == None:
            Log.E("Cannot evaluate expression")
        elif isinstance(tok, BoolToken):
            return tok.value
        elif isinstance(tok, IntToken):
            return 0 != tok.value
        else:
            Log.E("Expression of type '{}' is not convertible to bool".format(tok.TOKEN_TYPE))

new = ConfigSet
from pathlib import Path
from typing import Tuple

import lark
from lark import Transformer as LarkTransformer
from lark.lexer import Token

f = lark.Lark(open(Path(__file__).with_name("f.grammar")).read(), start="file")


def parse(text: str) -> lark.Tree:
    return f.parse(text)


class BaseFTransformer:
    def string(self, content: str):
        raise NotImplementedError

    def number(self, number: str):
        raise NotImplementedError

    def name(self, name: str):
        raise NotImplementedError

    def call(self, func, args: Tuple):
        raise NotImplementedError

    def code_block(self, parameter: Tuple, statements: Tuple, return_value):
        raise NotImplementedError

    def variadic_parameter(self, name: str):
        raise NotImplementedError

    def variadic_argument(self, name: str):
        raise NotImplementedError

    def list(self, content: str):
        raise NotImplementedError

    def file(self, statements: Tuple):
        raise NotImplementedError


class BaseFLarkTransformer(LarkTransformer):
    def ev_string(self, data: str):
        raise NotImplementedError

    def ev_number(self, data: str):
        raise NotImplementedError

    def ev_name(self, data: str):
        raise NotImplementedError

    def escaped_value(self, children):
        assert len(children) == 1
        c = children[0]
        if isinstance(c, Token):
            if c.type == "STRING":
                return self.ev_string(c.value)
            elif c.type == "NUMBER":
                return self.ev_number(c.value)
            else:
                return self.ev_name(c.value)
        return c

    def infix_operation(self, children):
        raise NotImplementedError

    def infix_operation_1(self, children):
        return self.infix_operation(children)

    def infix_operation_2(self, children):
        return self.infix_operation(children)

    def infix_operation_3(self, children):
        return self.infix_operation(children)

    def infix_operation_4(self, children):
        return self.infix_operation(children)

    def infix_operation_5(self, children):
        return self.infix_operation(children)

    def simple_call(self, children):
        raise NotImplementedError

    def empty_call(self, children):
        raise NotImplementedError

    def variadic_call(self, children):
        raise NotImplementedError

    def code_block(self, children):
        raise NotImplementedError

    def ex_code_block(self, children):
        return self.code_block(children)

    def ec_parameter(self, children):
        raise NotImplementedError

    def extended_call(self, children):
        raise NotImplementedError

    def parameter(self, children):
        raise NotImplementedError

    def assignment(self, children):
        raise NotImplementedError

    def prefix_operator(self, children):
        raise NotImplementedError

    def file(self, children):
        raise NotImplementedError

    def list(self, children):
        raise NotImplementedError

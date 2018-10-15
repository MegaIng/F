from collections import namedtuple
from pathlib import Path
from typing import Tuple

import lark
from lark import Transformer as LarkTransformer
from lark.lexer import Token

from f import util

f_parser = lark.Lark(open(Path(__file__).with_name("f.grammar")).read(), start="file")


def parse(text: str) -> lark.Tree:
    return f_parser.parse(text)


class BaseFTransformer:
    def string(self, content: str):
        raise NotImplementedError

    def number(self, number: str):
        raise NotImplementedError

    def name(self, name: str):
        raise NotImplementedError

    def call(self, func, args: Tuple):
        raise NotImplementedError

    def code_block(self, parameters: Tuple, statements: Tuple, return_value):
        raise NotImplementedError

    def parameter(self, name: str):
        raise NotImplementedError

    def variadic_parameter(self, name: str):
        raise NotImplementedError

    def variadic_value(self, value):
        raise NotImplementedError

    def list(self, content: Tuple):
        raise NotImplementedError

    def file(self, statements: Tuple):
        raise NotImplementedError

    def assignment(self, name: str, value):
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

    def variadic_value(self, children):
        raise NotImplementedError

    def code_block(self, children):
        raise NotImplementedError

    def ec_code_block(self, children):
        return self.code_block(children)

    def ec_parameters(self, children):
        raise NotImplementedError

    def extended_call(self, children):
        raise NotImplementedError

    def parameters(self, children):
        raise NotImplementedError

    def assignment(self, children):
        raise NotImplementedError

    def prefix_operator(self, children):
        raise NotImplementedError

    def file(self, children):
        raise NotImplementedError

    def list(self, children):
        raise NotImplementedError


_ec_parameters = namedtuple("_ec_parameters", "names values")
_parameters = namedtuple("_parameters", "content")


class FLarkTransformer(BaseFLarkTransformer):
    def __init__(self, transformer: BaseFTransformer):
        self.transformer = transformer

    def ev_string(self, data: str):
        return self.transformer.string(util.unescape_string(data[1:-1]))

    def ev_number(self, data: str):
        return self.transformer.number(data)

    def ev_name(self, data: str):
        return self.transformer.name(data)

    def infix_operation(self, children):
        left, operator, right, *tail = children
        left = self.transformer.call(self.transformer.name(operator.value), (left, right))
        while tail:
            operator, right, *tail = tail
            left = self.transformer.call(self.transformer.name(operator.value), (left, right))
        return left

    def simple_call(self, children):
        return self.transformer.call(children[0], tuple(children[1:]))

    def empty_call(self, children):
        return self.transformer.call(children[0], ())

    def variadic_value(self, children):
        if len(children) == 1:
            return self.transformer.variadic_value(self.transformer.name(children[0].value))
        else:
            return self.transformer.variadic_value(children[1])

    def code_block(self, children):
        if isinstance(children[0], _parameters):
            return self.transformer.code_block(children[0].content, tuple(children[1:-1]), children[-1])
        else:
            return self.transformer.code_block((), tuple(children[:-1]), children[-1])

    def ec_parameters(self, children):
        names = tuple(self.transformer.parameter(v.value) for v in children if isinstance(v, Token))
        values = tuple(v for v in children if not isinstance(v, Token))
        return _ec_parameters(names, values)

    def ec_code_block(self, children):
        return tuple(children)

    def extended_call(self, children):
        fun, *children, code_block = children
        (i, (parameters, values)), = ((i, v) for i, v in enumerate(children) if isinstance(v, _ec_parameters))
        return self.transformer.call(fun, (
            *children[:i],
            self.transformer.code_block(parameters, code_block[:-1], code_block[-1]),
            *values,
            *children[i + 1:]))

    def parameters(self, children):
        return _parameters(tuple(
            self.transformer.parameter(t.value) if not t.value.startswith(
                "...") else self.transformer.variadic_parameter(t.value)
            for t in children))

    def assignment(self, children):
        return self.transformer.assignment(children[0].value, children[1])

    def prefix_operator(self, children):
        return self.transformer.call(self.transformer.name(children[0].value), (children[1],))

    def file(self, children):
        return self.transformer.file(tuple(children))

    def list(self, children):
        return self.transformer.list(tuple(children))

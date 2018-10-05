from __future__ import annotations

import re
from collections import ChainMap
from decimal import Decimal
from typing import Tuple, Callable, Union

import lark
from lark import Transformer
from lark.lexer import Token

f = lark.Lark(open("f.grammar").read(), start="file")


class Interpreter:
    _variables: ChainMap = ChainMap({})

    @classmethod
    def add_layer(cls):
        # print("add_layer")
        cls._variables = cls._variables.new_child()

    @classmethod
    def remove_layer(cls):
        # print("remove_layer")
        cls._variables = cls._variables.parents

    @classmethod
    def set(cls, name: str, v: Value):
        # print("set", name, v)
        if name in cls._variables.maps[0]:
            raise NameError(f"'{name}' is already taken")
        else:
            cls._variables[name] = v

    @classmethod
    def get(cls, name: str):
        # print("get", name)
        if name not in cls._variables:
            raise NameError(name)
        else:
            return cls._variables[name]


class Statement:
    def execute(self) -> Value:
        raise NotImplementedError


class Assignment(Statement):
    def __init__(self, name: str, value: Value):
        self.name = name
        self.value = value

    def __repr__(self):
        return f"{self.name} = {self.value}"

    def execute(self):
        Interpreter.set(self.name, self.value.get())


class Value(Statement):
    def call(self, args: Tuple[Value, ...]):
        raise NotImplementedError

    def get(self) -> Value:
        raise NotImplementedError

    def execute(self):
        return self.get()


class Null(Value):
    def __repr__(self):
        return "Null"

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return self


Null = Null()


class Call(Value):
    def __init__(self, fun: Value, args: Tuple[Value, ...]):
        self.fun = fun
        self.args = args

    def __repr__(self):
        return f"{self.fun!r}({','.join(repr(a) for a in self.args)})"

    def call(self, args: Tuple[Value, ...]):
        return self.get().call(args)

    def get(self):
        return self.fun.call(tuple(arg.get() for arg in self.args))


class List(Value):
    def __init__(self, args: Tuple[Value, ...]):
        self.elements = list(args)

    def __repr__(self):
        return f"{{{', '.join(repr(a) for a in self.elements)}}}"

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return List(tuple(arg.get() for arg in self.elements))


class Number(Value):
    def __init__(self, number: Decimal):
        self.number = number

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.number == other.number

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return self

    def __repr__(self):
        return str(self.number)


class String(Value):
    def __init__(self, raw_string: str):
        assert raw_string[0] == raw_string[-1] == '"'
        self.raw_data = raw_string

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.data == other.data

    @property
    def data(self):
        return re.sub(r'\\(.)', r'\1', self.raw_data[1:-1])

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return self

    def __repr__(self):
        return self.raw_data


class Name(Value):
    def __init__(self, name: str):
        self.data = name

    def call(self, args: Tuple[Value, ...]):
        return self.get().call(args)

    def get(self):
        return Interpreter.get(self.data)

    def __repr__(self):
        return self.data


class CodeBlock(Value):
    def __init__(self, parameter: Tuple[str, ...], statements: Tuple[Statement, ...]):
        self.parameter = parameter
        self.statements = statements

    def __repr__(self):
        return "(" + ",".join(self.parameter) + "){" + ";".join(repr(s) for s in self.statements) + "}"

    def call(self, args: Tuple[Value, ...]):
        if len(args) != len(self.parameter):
            raise ValueError
        Interpreter.add_layer()
        for p, v in zip(self.parameter, args):
            Interpreter.set(p, v)
        ret = None
        for st in self.statements:
            ret = st.execute()
        Interpreter.remove_layer()
        return ret

    def get(self):
        return self


class BuiltinFunction(Value):
    def __init__(self, func: Callable, name: str):
        self.func = func
        self.name = name

    def __repr__(self):
        return f"<{self.name}>"

    def call(self, args: Tuple[Value, ...]):
        return self.func(*args)

    def get(self):
        return self


def f_function(arg: Union[Callable, str]):
    if callable(arg):
        ret = BuiltinFunction(arg, arg.__name__)
        Interpreter.set(ret.name, ret)
        return ret
    else:
        def inner(arg1: Callable):
            ret = BuiltinFunction(arg1, arg)
            Interpreter.set(ret.name, ret)
            return ret

        return inner


def f_constant(name: str, value: Value):
    Interpreter.set(name, value)


class FTransformer(Transformer):
    def escaped_value(self, children):
        assert len(children) == 1
        c = children[0]
        if isinstance(c, Token):
            if c.type == "STRING":
                return String(c.value)
            elif c.type == "NUMBER":
                return Number(Decimal(c.value))
            else:
                return Name(c.value)
        return c

    def statement(self, children):
        assert len(children) == 1
        return children[0]

    def infix_operation(self, children):
        v = Call(Name(children[1].value), (children[0], children[2]))
        if len(children) > 3:
            return self.infix_operation((v, *children[3:]))
        else:
            return v

    infix_operation_1 = infix_operation_2 = infix_operation_3 = infix_operation_4 = infix_operation_5 = infix_operation

    def simple_call(self, children):
        return Call(children[0], tuple(children[1:]))

    def empty_call(self, children):
        return Call(children[0], ())

    def code_block(self, children):
        if isinstance(children[0], tuple):
            return CodeBlock(children[0], tuple(children[1:]))
        else:
            return CodeBlock((), tuple(children))

    ec_code_block = code_block

    def ec_parameter(self, children):
        names = tuple(v.value for v in children if isinstance(v, Token))
        values = tuple(v for v in children if isinstance(v, Value))
        return names, values

    def extended_call(self, children):
        fun, *children, code_block = children
        (i, (code_block.parameter, values)), = ((i, v) for i, v in enumerate(children) if isinstance(v, tuple))
        return Call(fun, (*children[:i], code_block, *values, *children[i + 1:]))

    def parameter(self, children):
        return tuple(p.value for p in children)

    def assignment(self, children):
        assert len(children) == 2
        return Assignment(children[0].value, children[1])

    def prefix_operator(self, children):
        assert len(children) == 2
        return Call(Name(children[0].value), (children[1],))

    def file(self, children):
        return CodeBlock((), tuple(children))

    def list(self, children):
        return List(children)


import stdlib

stdlib.finish_init()

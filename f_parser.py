from __future__ import annotations

import re
from decimal import Decimal
from typing import Tuple, Callable, Union, Iterable, Dict, Optional

import lark
from lark import Transformer
from lark.lexer import Token
from lark.tree import pydot__tree_to_png

f = lark.Lark(open("f.grammar").read(), start="file")


class Frame:
    def __init__(self, parent: Optional[Frame]):
        self.parent = parent
        self.variables: Dict[str, Value] = {}

    def get(self, name: str):
        try:
            return self.variables[name]
        except KeyError:
            if self.parent is None:
                raise NameError(name) from None
        return self.parent.get(name)

    def set(self, name: str, value: Value):
        if name in self.variables:
            raise NameError(f"'{name}' is already taken")
        else:
            self.variables[name] = value


class Interpreter:
    frames = [Frame(None)]

    @classmethod
    def add_frame(cls, frame: Frame = None):
        if frame is None:
            frame = Frame(cls.frames[-1])
        cls.frames.append(frame)
        return frame

    @classmethod
    def remove_frame(cls):
        f = cls.frames.pop()
        return f

    @classmethod
    def set(cls, name: str, v: Value):
        cls.frames[-1].set(name, v)

    @classmethod
    def get(cls, name: str):
        return cls.frames[-1].get(name)


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
        return f"{self.fun!r}({', '.join(repr(a) for a in self.args)})"

    def call(self, args: Tuple[Value, ...]):
        return self.get().call(args)

    def get(self):
        return self.fun.call(tuple(arg.get() for arg in self.args))


class VariadicCall(Value):
    def __init__(self, fun: Value, pre_args: Tuple[Value, ...], post_args: Tuple[Value, ...]):
        self.post_args = tuple(post_args)
        self.pre_args = tuple(pre_args)
        self.fun = fun

    def __repr__(self):
        return f"{self.fun!r}({', '.join(str(a) for a in self.pre_args+('...',)+self.post_args)})"

    def call(self, args: Tuple[Value, ...]):
        return self.get().call(args)

    def get(self):
        return self.fun.call(
            tuple(arg.get() for arg in (*self.pre_args, *Interpreter.get('...').elements, *self.post_args)))


class List(Value):
    def __init__(self, args: Iterable[Value, ...]):
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

    def __ge__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.number >= other.number

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.number > other.number

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.number < other.number

    def __le__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.number <= other.number

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return self

    def __repr__(self):
        return str(self.number)


escaped_values = {
    "a": "\a",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
    "\\": "\\",
    "\'": "\'",
    "\"": "\"",
    "\n": ""
}


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
    def __init__(self, parameter: Iterable[str, ...], statements: Iterable[Statement, ...], parent_frame: Frame = None):
        self.parameter = tuple(parameter)
        self.statements = tuple(statements)
        self.parent_frame = parent_frame

    def __repr__(self):
        return "(" + ", ".join(self.parameter) + "){" + ";".join(repr(s) for s in self.statements) + "}"

    def _apply_arguments(self, arguments: Tuple[Value, ...]):
        if '...' not in self.parameter:
            if len(arguments) != len(self.parameter):
                raise ValueError(f"Not enough arguments (Expected {len(self.parameter)}, got {len(arguments)})")
            for p, a in zip(self.parameter, arguments):
                Interpreter.set(p, a)
        else:
            i = self.parameter.index('...')
            pre, post = self.parameter[:i], self.parameter[i + 1:]
            if len(arguments) < len(pre) + len(post):
                raise ValueError(f"Not enough arguments (Expected at least {len(pre)+len(post)}, got {len(arguments)})")
            arg_pre, arg_post = arguments[:len(pre)], (arguments[-len(post):] if post else ())
            arg_var = (arguments[len(pre):-len(post)] if post else arguments[len(pre):])
            for p, a in zip(pre + post, arg_pre + arg_post):
                Interpreter.set(p, a)
            Interpreter.set('...', List(arg_var))

    def call(self, args: Tuple[Value, ...], implicit_print=False, scoped=True):
        if not scoped and self.parameter:
            raise ValueError("CodeBlocks with parameter have to be scoped")
        if scoped:
            if self.parent_frame is None:
                Interpreter.add_frame()
            else:
                Interpreter.add_frame(Frame(self.parent_frame))
            self._apply_arguments(args)
        ret = None
        for st in self.statements:
            ret = st.execute()
            if implicit_print:
                print(ret)
        if scoped:
            Interpreter.remove_frame()
        return ret

    def get(self):
        if self.parent_frame is not None:
            return self
        else:
            return self.__class__(self.parameter, self.statements, Interpreter.frames[-1])


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

    def variadic_call(self, children):
        i, = (i for i, v in enumerate(children) if isinstance(v, Token) and v.value == '...')
        return VariadicCall(children[0], children[1:i], children[i + 1:])

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


def parse(data: str) -> CodeBlock:
    tree = f.parse(data)
    pydot__tree_to_png(tree, "test.png")
    return FTransformer().transform(tree)


import f_builtin

f_builtin.finish_init()

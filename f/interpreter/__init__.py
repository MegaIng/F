from __future__ import annotations

from decimal import Decimal
from typing import Tuple, Callable, Union, Iterable, Dict, Optional

import f
from f.grammar import FLarkTransformer


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
        return cls.frames.pop()

    @classmethod
    def set(cls, name: str, v: Value):
        cls.frames[-1].set(name, v)

    @classmethod
    def get(cls, name: str):
        return cls.frames[-1].get(name)


class Statement:
    def execute(self) -> Value:
        raise NotImplementedError


class Value(Statement):
    def call(self, args: Tuple[Value, ...]):
        raise NotImplementedError

    def get(self) -> Value:
        raise NotImplementedError

    def execute(self):
        return self.get()


class Assignment(Value):
    def __init__(self, name: str, value: Value):
        self.name = name
        self.value = value

    def __repr__(self):
        return f"{self.name} = {self.value}"

    def call(self, args: Tuple[Value, ...]):
        return self.get().call(args)

    def get(self):
        v = self.value.get()
        Interpreter.set(self.name, v)
        return v


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
        args = ', '.join(repr(a) for a in self.args)
        return f"{self.fun!r}({args})"

    def call(self, args: Tuple[Value, ...]):
        return self.get().call(args)

    def get(self):
        return self.fun.call(tuple(arg.get() for arg in unpack_arguments(self.args)))


class VariadicValue(Value):
    def __init__(self, value: Value):
        self.value = value

    def __repr__(self):
        return f"...({self.value!r})"

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self) -> Value:
        raise ValueError


def unpack_arguments(arguments: Tuple[Value, ...]) -> Tuple[Value, ...]:
    return tuple(e
                 for a in arguments
                 for e in (a.value.get().elements if isinstance(a, VariadicValue) else (a,)))


class List(Value):
    def __init__(self, args: Iterable[Value, ...]):
        self.elements = tuple(args)

    def __repr__(self):
        elements = ', '.join(repr(a) for a in self.elements)
        return f"[{elements}]"

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return List(tuple(arg.get() for arg in unpack_arguments(self.elements)))


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
    "b": "\b",
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
    def __init__(self, data: str):
        self.data = data

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.data == other.data

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return self

    def __repr__(self):
        return self.data


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
    def __init__(self, parameters: Iterable[str, ...], statements: Iterable[Statement, ...],
                 parent_frame: Frame = None):
        self.parameters = tuple(parameters)
        self.statements = tuple(statements)
        self.parent_frame = parent_frame

    def __repr__(self):
        return "(" + ", ".join(self.parameters) + "){" + ";".join(repr(s) for s in self.statements) + "}"

    def _apply_arguments(self, arguments: Tuple[Value, ...]):
        if not any(p.startswith("...") for p in self.parameters):
            if len(arguments) != len(self.parameters):
                raise ValueError(f"Not enough arguments (Expected {len(self.parameters)}, got {len(arguments)})")
            for p, a in zip(self.parameters, arguments):
                Interpreter.set(p, a)
        else:
            (i, vp), = ((i, p) for i, p in enumerate(self.parameters) if p.startswith("..."))
            pre, post = self.parameters[:i], self.parameters[i + 1:]
            if len(arguments) < len(pre) + len(post):
                raise ValueError(f"Not enough arguments (Expected at least {len(pre)+len(post)}, got {len(arguments)})")
            arg_pre, arg_post = arguments[:len(pre)], (arguments[-len(post):] if post else ())
            arg_var = (arguments[len(pre):-len(post)] if post else arguments[len(pre):])
            for p, a in zip(pre + post, arg_pre + arg_post):
                Interpreter.set(p, a)
            Interpreter.set('...' if vp == '...' else vp[3:], List(arg_var))

    def call(self, args: Tuple[Value, ...], implicit_print=False, scoped=True):
        if not scoped and self.parameters and self.parameters != ('...',):
            raise ValueError("CodeBlocks with parameters have to be scoped")
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
            return self.__class__(self.parameters, self.statements, Interpreter.frames[-1])


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
            func = BuiltinFunction(arg1, arg)
            Interpreter.set(func.name, func)
            return func

        return inner


def f_constant(name: str, value: Value):
    Interpreter.set(name, value)


class FInterpreterTransformer(f.BaseFTransformer):
    def string(self, content: str):
        return String(content)

    def number(self, number: str):
        return Number(Decimal(number))

    def name(self, name: str):
        return Name(name)

    def call(self, func, args: Tuple):
        return Call(func, args)

    def code_block(self, parameters: Tuple, statements: Tuple, return_value):
        return CodeBlock(parameters, (*statements, return_value), None)

    def parameter(self, name: str):
        return name

    def variadic_parameter(self, name: str):
        return name

    def variadic_value(self, value):
        return VariadicValue(value)

    def list(self, content: Tuple):
        return List(content)

    def file(self, statements: Tuple):
        return CodeBlock(('...',), statements)

    def assignment(self, name: str, value):
        return Assignment(name, value)


def f_compile(data: str, debug=0) -> CodeBlock:
    tree = f.parse(data)
    if debug > 0:
        from lark.tree import pydot__tree_to_png
        pydot__tree_to_png(tree, 'debug.png')
    return FLarkTransformer(FInterpreterTransformer()).transform(tree)


def f_eval(data: str, argv: Tuple[str, ...] = (), debug=0):
    code = f_compile(data, debug - 1)
    if debug:
        print(code)
    code.call(tuple(String(s) for s in argv))


from . import builtins

builtins.finish_init()

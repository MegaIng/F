import operator
from dataclasses import dataclass
from functools import reduce
from typing import Tuple, IO

from f.interpreter import f_function, Value, CodeBlock, Number, List, Null, f_constant, Interpreter, f_compile, String


class Reference(Value):
    def __init__(self, data: Value):
        self.data = data

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return self


class Boolean(Value):
    _true_value = None
    _false_value = None

    def __new__(cls, arg):
        if arg:
            return cls._true_value
        else:
            return cls._false_value

    def __repr__(self):
        return "true" if self else "false"

    def __bool__(self):
        return self is self._true_value

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return self


Boolean._true_value = super(Boolean, Boolean).__new__(Boolean)
Boolean._false_value = super(Boolean, Boolean).__new__(Boolean)

f_constant('true', Boolean._true_value)
f_constant('false', Boolean._false_value)
f_constant('Null', Null)


@f_function
def reference(data: Value) -> Value:
    return Reference(data)


@f_function("!")
def dereference(data: Reference) -> Value:
    return data.data


@f_function("<-")
def store_in_reference(var: Reference, data: Value) -> Value:
    var.data = data
    return Null


@f_function("while")
def while_(condition: CodeBlock, action: CodeBlock) -> List:
    ret = []
    while condition.call(()):
        ret.append(action.call(()))
    return List(ret)


@f_function
def either(condition: CodeBlock, a: Value, b: Value) -> Value:
    return a if condition.get() else b


@f_function
def foreach(action: CodeBlock, *args: List) -> List:
    return List(action.call(v) for v in zip(*(l.elements for l in args)))


@f_function("=")
def eq(first: Value, second: Value) -> Value:
    return Boolean(first == second)


@f_function(">=")
def ge(first: Value, second: Value) -> Value:
    return Boolean(first >= second)


@f_function(">")
def gt(first: Value, second: Value) -> Value:
    return Boolean(first > second)


@f_function("<")
def lt(first: Value, second: Value) -> Value:
    return Boolean(first < second)


@f_function("<=")
def le(first: Value, second: Value) -> Value:
    return Boolean(first <= second)


@f_function("not")
def not_(data: Value) -> Value:
    return Boolean(not data)


@f_function("and")
def and_(*args: Value) -> Value:
    return Boolean(all(arg.call(()) if isinstance(arg, CodeBlock) else arg.get() for arg in args))


@f_function("all")
def all_(*args: Value) -> Value:
    return Boolean(all(arg.call(()) if isinstance(arg, CodeBlock) else arg.get() for arg in args))


@f_function("any")
def any_(*args: Value) -> Value:
    return Boolean(any(arg.call(()) if isinstance(arg, CodeBlock) else arg.get() for arg in args))


@f_function("or")
def or_(*args: Value) -> Value:
    return Boolean(any(arg.call(()) if isinstance(arg, CodeBlock) else arg.get() for arg in args))


@f_function("do")
def do(fun: Value, *args: Value) -> Value:
    return fun.call(args)


@f_function("*")
def mul(*args: Number) -> Value:
    return Number(reduce(operator.mul, (arg.number for arg in args)))


@f_function("**")
def mul(*args: Number) -> Value:
    return Number(reduce(operator.mul, (arg.number for arg in args)))


@f_function("-")
def sub(*args: Number) -> Value:
    return Number(reduce(operator.sub, (arg.number for arg in args)))


@f_function("+")
def add(*args: Number) -> Value:
    return Number(reduce(operator.add, (arg.number for arg in args)))


@f_function("print")
def print_(*args: Value) -> Value:
    print(*args)
    return Null


@dataclass
class IOReference(Value):
    file: IO

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self) -> Value:
        return self


@f_function
def withOpenFile(action: CodeBlock, file_name: String, mode: String) -> Value:
    with open(file_name.data, mode.data) as f:
        return action.call((IOReference(f),))


@f_function
def writeLine(f: IOReference, line: String) -> Value:
    f.file.write(line.data + "\n")
    return Null


@f_function
def get(data: List, index: Number) -> Value:
    if not index.number % 1 == 0:
        raise ValueError
    return data.elements[int(index.number)]


@f_function
def append(data: List, new: Value) -> List:
    return List(data.elements + [new])


@f_function
def insert(data: List, index: Number, value: Value) -> List:
    if not index.number % 1 == 0:
        raise ValueError
    return List(data.elements[:int(index.number)] + [value] + data.elements[int(index.number):])


def finish_init():
    Interpreter.add_frame()
    f_compile(open("stdlib.f").read()).call((), scoped=False)

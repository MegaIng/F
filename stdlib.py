import operator
from decimal import Decimal
from functools import reduce
from typing import Tuple

from f import f_function, Value, CodeBlock, Number


class Reference(Value):
    def __init__(self, data: Value):
        self.data = data

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return self


class Boolean(Value):
    def __init__(self, data: bool):
        self.data = data

    def __repr__(self):
        return "true" if self.data else "false"

    def __bool__(self):
        return self.data

    def call(self, args: Tuple[Value, ...]):
        raise TypeError

    def get(self):
        return self


@f_function
def reference(data: Value) -> Value:
    return Reference(data)


@f_function("!")
def dereference(data: Reference) -> Value:
    return data.data


@f_function("<-")
def store_in_reference(var: Reference, data: Value) -> Value:
    var.data = data
    return var


@f_function("while")
def while_(condition: CodeBlock, action: CodeBlock) -> Value:
    ret = None
    while condition.call(()):
        ret = action.call(())
    return ret


@f_function("=")
def equal(first: Value, second: Value) -> Value:
    return Boolean(first == second)


@f_function("not")
def not_(data: Value) -> Value:
    return Boolean(not data)


@f_function("do")
def do_(function: Value, *args: Value) -> Value:
    return function.call(args)


@f_function("*")
def mul(*args: Number) -> Value:
    return Number(reduce(operator.mul, (arg.number for arg in args)))


@f_function("-")
def sub(*args: Number) -> Value:
    return Number(reduce(operator.sub, (arg.number for arg in args)))

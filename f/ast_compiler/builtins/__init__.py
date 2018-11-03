import operator
from functools import reduce
from typing import Callable

f_globals = {"__builtins__": {}}


def f_function(arg):
    if callable(arg):
        f_globals["__builtins__"][arg.__name__] = arg
        return arg
    else:
        def inner(arg1):
            f_globals["__builtins__"][arg] = arg1
            return arg1

        return inner


def f_constant(name, value):
    f_globals["__builtins__"][name] = value


class Reference:
    def __init__(self, data):
        self.data = data


Null = None
true = True
false = False

f_constant('true', true)
f_constant('false', false)
f_constant("Null", Null)


@f_function
def reference(data):
    return Reference(data)


@f_function("!")
def dereference(data):
    return data.data


@f_function("<-")
def store_in_reference(var, data):
    var.data = data
    return Null


@f_function("while")
def while_(condition, action):
    ret = []
    while condition():
        ret.append(action())
    return ret


@f_function
def either(condition, a, b):
    return a if condition else b


@f_function
def foreach(action, *args):
    return [action(*v) for v in zip(*args)]


@f_function("=")
def eq(first, second):
    return first == second


@f_function(">=")
def ge(first, second):
    return first >= second


@f_function(">")
def gt(first, second):
    return first > second


@f_function("<")
def lt(first, second):
    return first < second


@f_function("<=")
def le(first, second):
    return first <= second


@f_function("not")
def not_(data):
    return not data


@f_function("and")
@f_function("all")
def and_(*args):
    return all(arg() if isinstance(arg, Callable) else arg for arg in args)


@f_function("any")
@f_function("or")
def or_(*args):
    return any(arg() if isinstance(arg, Callable) else arg for arg in args)


@f_function(";")
def _semicolon(*values):
    return values[-1]


@f_function("do")
def do(fun, *args):
    return fun(*args)


@f_function("*")
def mul(*args):
    return reduce(operator.mul, (arg for arg in args))


@f_function("**")
def mul(*args):
    return reduce(operator.pow, (arg for arg in args))


@f_function("-")
def sub(*args):
    return reduce(operator.sub, (arg for arg in args))


@f_function("+")
def add(*args):
    return reduce(operator.add, (arg for arg in args))


@f_function("print")
def print_(*args):
    print(*args)
    return Null


@f_function("withOpenFile")
def with_open_file(action, file_name, mode):
    with open(file_name, mode) as f:
        return action(f)


@f_function("writeLine")
def write_line(f, line):
    f.write(line + "\n")
    return Null


@f_function
def get(data, index):
    if not index % 1 == 0:
        raise ValueError
    return data.elements[int(index)]


@f_function
def append(data, new):
    return data + [new]


@f_function
def insert(data, index, value):
    if not index % 1 == 0:
        raise ValueError
    return data[:int(index)] + [value] + data[int(index):]

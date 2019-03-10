from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Iterator, Set, Dict


class FAST:
    scope: Scope = None  # the scope they are in

    def _pretty(self, indent) -> Iterator[str]:
        raise NotImplementedError

    def pretty(self, indent='  '):
        return '\n'.join(self._pretty(indent))

    def to_c(self, context):
        raise NotImplementedError


class FValue(FAST):
    def _pretty(self, indent) -> Iterator[str]:
        raise NotImplementedError

    def to_c(self, context) -> str:
        raise NotImplementedError(f"to_c() not implemented by {self.__class__}")


@dataclass
class FString(FValue):
    data: str

    def _pretty(self, indent):
        yield f"{type(self).__name__}: {self.data!r}"

    def to_c(self, context):
        return f"string(\"{self.data}\")"


@dataclass
class FName(FValue):
    name: str

    def _pretty(self, indent):
        yield f"{type(self).__name__}: {self.name}"

    def to_c(self, context):
        return self.scope.lookup(self.name)


@dataclass
class FNumber(FValue):
    data: float

    def _pretty(self, indent):
        yield f"{type(self).__name__}: {self.data}"

    def to_c(self, context):
        return f"number({self.data})"


@dataclass
class FCall(FValue):
    func: FValue
    arguments: Tuple[FValue, ...]

    def _pretty(self, indent: str):
        yield f"{type(self).__name__}:"
        yield from (indent + line for line in self.func._pretty(indent))
        yield f"{indent}Arguments:"
        for i, arg in enumerate(self.arguments):
            yield from (indent * 2 + line for line in arg._pretty(indent))

    def to_c(self, context):
        f = self.func.to_c(context)
        if isinstance(f, NamedReference):
            if f.is_builtin:
                if f.raw == ';':
                    for s in self.arguments[:-1]:
                        context.push_simple(str(s.to_c(context)))
                    return self.arguments[-1].to_c(context)
                elif f.raw == 'if':
                    temp_name = context.temp_var()
                    context.push_simple(f'{t_object} {temp_name}')
                    context.start_compound(f'if(truthy({self.arguments[0].to_c(context)}))', '')
                    context.push_simple(f'{temp_name} = call({self.arguments[1].to_c(context)}, list(0))')
                    context.end_compound()
                    context.start_compound('else', '')
                    context.push_simple(f'{temp_name} = call({self.arguments[2].to_c(context)}, list(0))')
                    context.end_compound()
                    return temp_name
                elif f.raw == 'do':
                    if len(self.arguments) > 0 and not isinstance(self.arguments[0], FVariadicValue):
                        temp_var = context.temp_var()
                        context.push_simple(f"{t_object} {temp_var} = call({self.arguments[0].to_c(context)}, "
                                            f"{FList(self.arguments[1:]).to_c(context)})")
                        return temp_var
        temp_var = context.temp_var()
        context.push_simple(f"{t_object} {temp_var} = call({f}, {FList(self.arguments).to_c(context)})")
        return temp_var


@dataclass
class FVariadicValue(FValue):
    value: FValue

    def to_c(self, context):
        return f"variadic({self.value.to_c(context)})"


@dataclass
class FCodeBlock(FValue):
    parameters: Tuple[str, ...]
    value: FValue
    variadic_parameter: Tuple[int, str] = None
    scope: Scope = None
    inner_scope: Scope = None

    def _pretty(self, indent: str):
        yield f"{type(self).__name__}:"
        yield f"{indent}Parameters: ({','.join(self.parameters)})"
        if self.variadic_parameter is not None:
            yield f"{indent}Variadic: {self.variadic_parameter}"
        yield f"{indent}Value:"
        yield from (indent * 2 + line for line in self.value._pretty(indent))
        if self.scope is not None:
            yield f"{indent}Scope:"
            yield f"{indent * 2}Used: {self.inner_scope.used!r}"
            yield f"{indent * 2}Defined: {self.inner_scope.defined!r}"

    def to_c(self, context):
        name = context.start_function(self.inner_scope)
        if self.variadic_parameter is not None:
            for i, n in enumerate(self.parameters[:self.variadic_parameter[0]]):
                context.push_simple(f"self.{n} = args->list.elements[{i}]")
            pre = self.variadic_parameter[0]
            post = len(self.parameters) - pre
            context.push_simple(f"self.{self.variadic_parameter[1]} = sublist(args, {pre}, args->list.count - {post})")
            for i, n in enumerate(self.parameters[self.variadic_parameter[0]:][::-1]):
                context.push_simple(f"self.{n} = args->list.elements[args.list.count - {i + 1}]")
        else:
            for i, n in enumerate(self.parameters):
                context.push_simple(f"self.{n} = args->list.elements[{i}]")
        context.push_simple(f"return {self.value.to_c(context)}")
        context.end_function()
        if self.inner_scope.outer:
            outer_vars = ', '.join(f'.{self.scope.lookup(n).name} = {self.scope.lookup(n)}'
                                   for n in self.inner_scope.outer)
            temp = context.temp_var()
            context.push_simple(f"struct _outer_{name} {temp} = {{{outer_vars}}};")
            return f"callable(copied(&{temp}, sizeof({temp})), ({t_function}) {name})"
        else:
            return f"callable(NULL, ({t_function}) {name})"


@dataclass
class FList(FValue):
    values: Tuple[FValue, ...]

    def _pretty(self, indent: str):
        yield f"{type(self).__name__}:"
        for i, v in enumerate(self.values):
            yield from (indent + line for line in v._pretty(indent))

    def to_c(self, context):
        if not self.values:
            return "list(0)"
        return f"list_v({len(self.values)}, {', '.join(str(v.to_c(context)) for v in self.values)})"


@dataclass
class FModule(FAST):
    statements: Tuple[FValue, ...]

    def _pretty(self, indent: str):
        yield f"{type(self).__name__}:"
        for i, v in enumerate(self.statements):
            yield from (indent + line for line in v._pretty(indent))

    def to_c(self, context):
        raise TypeError

    def generate_c(self):
        context = CompilerContext()
        _walk_ast(context, self)
        cc = CBuilder()
        cc.target_stack[0].scope = self.scope
        for s in self.statements:
            cc.push_simple(s.to_c(cc))
        cc.end_function()
        return cc.to_c()


@dataclass
class FAssignment(FValue):
    name: str
    value: FValue

    def _pretty(self, indent: str):
        yield f"{type(self).__name__}:"
        yield f"{indent}Target: {self.name}"
        yield f"{indent}Value:"
        yield from (indent * 2 + line for line in self.value._pretty(indent))

    def to_c(self, context: CBuilder):
        v = self.scope.lookup(self.name)
        context.push_simple(f"{v} = {self.value.to_c(context)}")
        return v


_operators = {
    ';': 'operators.semicolon',

    '+': 'operators.add',
    '-': 'operators.sub',
    '*': 'operators.mul',
    '/': 'operators.div',
    '**': 'operators.pow',

    '=': 'operators.eq',
    '!=': 'operators.ne',
    '>': 'operators.gt',
    '>=': 'operators.ge',
    '<': 'operators.lt',
    '<=': 'operators.le',

    '<-': 'operators.store',
    '!': 'operators.load',
}
_keywords = {'if', 'else', 'while', 'do', 'false', 'true'}


@dataclass
class NamedReference:
    raw: str
    is_builtin: bool  # Could not be resolved, is never defined
    is_local: bool  # Was defined on the same level

    @property
    def name(self):
        assert self.raw not in _operators
        return self.raw + "_" if self.raw in _keywords else self.raw

    def __str__(self):
        assert not self.raw.startswith('...')
        if self.is_local:
            return f"self.{self.name}"
        elif not self.is_builtin:
            return f"outer->{self.name}"
        elif self.raw in _operators:
            return _operators[self.raw]
        else:
            return f"builtins.{self.name}"

    @property
    def is_outer(self):
        return (not self.is_local) and (not self.is_builtin)


@dataclass
class Scope:
    used: Set[str] = field(default_factory=set)
    defined: Dict[str, int] = field(default_factory=dict)
    parent: Scope = None

    def lookup(self, name: str) -> NamedReference:
        # assert name in self.used, (name, self.used)
        if name in self.defined:
            return NamedReference(name, False, True)
        elif self.parent is None:
            return NamedReference(name, True, False)
        else:
            n = self.parent.lookup(name)
            n.is_local = False
            return n

    @property
    def outer(self):
        return {n for n in self.used if self.lookup(n).is_outer}


@dataclass
class CompilerContext:
    current_scope: Scope = field(default_factory=Scope)

    def add_scope(self) -> Scope:
        self.current_scope = Scope(parent=self.current_scope)
        return self.current_scope

    def pop_scope(self):
        if self.current_scope.parent is None:
            raise ValueError("Can't pop global scope")
        self.current_scope = self.current_scope.parent

    def variable_used(self, name: str):
        self.current_scope.used.add(name)

    def variable_defined(self, name: str):
        if name in self.current_scope.defined:
            raise ValueError("Can't redefine variable")
        self.current_scope.defined[name] = len(self.current_scope.defined)


def _walk_ast(cc: CompilerContext, ast: FAST):
    assert ast.scope is None
    ast.scope = cc.current_scope
    if isinstance(ast, FName):
        cc.variable_used(ast.name)
    elif isinstance(ast, FAssignment):
        cc.variable_defined(ast.name)
        _walk_ast(cc, ast.value)
    elif isinstance(ast, FCodeBlock):
        ast.inner_scope = cc.add_scope()
        for p in ast.parameters:
            cc.variable_defined(p)
        if ast.variadic_parameter is not None:
            cc.variable_defined(ast.variadic_parameter[1])
        _walk_ast(cc, ast.value)
        cc.pop_scope()
        cc.current_scope.used.update(ast.inner_scope.outer)
    elif isinstance(ast, FList):
        for v in ast.values:
            _walk_ast(cc, v)
    elif isinstance(ast, FCall):
        for c in (ast.func, *ast.arguments):
            _walk_ast(cc, c)
    elif isinstance(ast, (FString, FNumber)):
        pass
    elif isinstance(ast, FModule):
        assert cc.current_scope.parent is None
        for s in ast.statements:
            _walk_ast(cc, s)
    elif isinstance(ast, FVariadicValue):
        _walk_ast(cc, ast.value)
    else:
        raise ValueError(ast)


from f.c_compiler.c_compiler import CBuilder, t_object, t_function

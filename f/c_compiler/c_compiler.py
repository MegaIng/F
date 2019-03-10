from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

TEMPLATE = r"""
#include "f_runtime.c"

%FUNCTIONS%
"""


class Statement:
    def to_c(self, indent: int):
        raise NotImplementedError


@dataclass
class SingleLine(Statement):
    line: str

    def to_c(self, indent: int):
        if '(' in self.line or '=' in self.line or 'return' in self.line:
            return ' ' * indent + self.line + ';\n'
        else:
            return ''  # This line is neither a call, nor an assignment, nor a return


class Target:
    statements: List[Statement]


@dataclass
class CompoundStatement(Statement, Target):
    open: str
    statements: List[Statement]
    close: str

    def to_c(self, indent: int):
        out = ' ' * indent + self.open + '{\n'
        for s in self.statements:
            out += s.to_c(indent + 4)
        out += ' ' * indent + "}\n"
        return out


@dataclass
class Function(Target):
    name: str
    statements: List[Statement]
    scope: Scope
    temp_var_counter = 0

    def to_c(self):
        out = ""
        if self.name == 'main':
            out += 'int main(int argc, char** argv) {\n'
            out += '    setup(argc, argv);\n'
            # assert set(self.scope.defined).issuperset(self.scope.used), (self.scope.defined, self.scope.used)
        else:
            if self.scope.outer:
                outer_vars = '\n    '.join(f"{t_object} {self.scope.lookup(n).name.rpartition('.')[2]};"
                                           for n in self.scope.outer)
                out += f"struct _outer_{self.name} {{\n{outer_vars}\n}};\n"
                out += f"{t_object} {self.name}(struct _outer_{self.name}* outer, {t_object} args) {{\n"
            else:
                out += f"{t_object} {self.name}(void* UNUSED(outer), {t_object} args) {{\n"

        if self.scope.defined:
            self_vars = '\n     '.join(f"{t_object} {self.scope.lookup(n).name.rpartition('.')[2]};"
                                       for n in self.scope.defined)
            out = f"struct _self_{self.name} {{\n    {self_vars}\n}};\n" + out  # prepend
            out += f'    struct _self_{self.name} self;\n'
        for s in self.statements:
            out += s.to_c(4)
        out += "}\n\n"
        return out


@dataclass
class CBuilder:
    functions: List[Function] = field(default_factory=list)
    target_stack: List[Target] = field(default_factory=lambda: [Function('main', [], None)])
    function_counter = 0

    def start_function(self, scope: Scope):
        name = f"f{self.function_counter:08X}"
        self.function_counter += 1
        self.target_stack.append(Function(name, [], scope))
        return name

    def end_function(self):
        assert isinstance(self.target_stack[-1], Function)
        self.functions.append(self.target_stack.pop())

    def start_compound(self, o: str, c: str):
        self.target_stack.append(CompoundStatement(o, [], c))

    def end_compound(self):
        assert isinstance(self.target_stack[-1], CompoundStatement)
        top = self.target_stack.pop()
        self.target_stack[-1].statements.append(top)

    def push_simple(self, data: str):
        self.target_stack[-1].statements.append(SingleLine(data))

    def temp_var(self):
        *_, f = (f for f in self.target_stack if isinstance(f, Function))
        n = f"temp_{f.temp_var_counter:04X}"
        f.temp_var_counter += 1
        return n

    def to_c(self) -> str:
        out = ""
        for f in self.functions:
            out += f.to_c()
        return TEMPLATE.replace('%FUNCTIONS%', out)


t_object = 'f_object'
tp_object = t_object + '*'
t_function = 'function_type'

from f.c_compiler.fast import Scope

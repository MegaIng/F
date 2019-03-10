from pathlib import Path
from typing import Tuple

from f.c_compiler.fast import CompilerContext, _walk_ast, FVariadicValue
from f.grammar import BaseFTransformer, FLarkTransformer, parse
from general_c_compiler import get_compiler
from .fast import FName, FAST, FAssignment, FCall, FCodeBlock, FList, FModule, FNumber, FString, FValue


class ASTTransformer(BaseFTransformer):
    def string(self, content: str):
        return FString(content)

    def number(self, number: str):
        return FNumber(float(number))

    def name(self, name: str):
        if name.startswith('...'):
            return FName(name[3:] if len(name) > 3 else '_dot_dot_dot')
        return FName(name)

    def call(self, func, args: Tuple):
        return FCall(func, args)

    def code_block(self, parameters: Tuple, statements: Tuple, return_value):
        assert len(statements) == 0
        if any(isinstance(p, tuple) for p in parameters):
            i, = (i for i, v in enumerate(parameters) if isinstance(v, tuple))
            return FCodeBlock(parameters[:i] + parameters[i + 1:], return_value, (i, parameters[i][1]))
        else:
            return FCodeBlock(parameters, return_value)

    def parameter(self, name: str):
        return name

    def variadic_parameter(self, name: str):
        return 'variadic', (name[3:] if len(name) > 3 else '_dot_dot_dot')

    def variadic_value(self, value):
        return FVariadicValue(value)

    def list(self, content: Tuple):
        return FList(content)

    def file(self, statements: Tuple):
        return FModule(statements)

    def assignment(self, name: str, value):
        return FAssignment(name, value)


def f_compile(source: str, out_file: Path = None):
    ast: FModule = FLarkTransformer(ASTTransformer()).transform(parse(source))
    c_source = ast.generate_c()
    with (Path(__file__).with_name('main.c')).open('w') as f:
        f.write(c_source)
    compiler = get_compiler()
    compiler.compile_to_executable(Path(__file__).with_name('main.c'), out_file)

import ast
from collections import namedtuple
from typing import Tuple, List

import f
from f.grammar import FLarkTransformer

_varpar = namedtuple("_vararg", "content")


class FASTTransformer(f.BaseFTransformer):
    def make_statements(self, nodes: Tuple[Tuple[Tuple[ast.AST, ...], ast.AST], ...]) -> List[ast.AST]:
        return [n for st, e in nodes for n in ((*st, ast.Expr(e)) if e is not None else st)]

    def string(self, content: str):
        return (), ast.Str(content)

    def number(self, number: str):
        return (), ast.Num(float(number))

    def name(self, name: str):
        return (), ast.Name(name, ast.Load())

    def parameter(self, name: str):
        return (), ast.arg(name, None)

    def variadic_parameter(self, name: str):
        return (), _varpar(ast.arg(name, None))

    def call(self, func, args: Tuple):
        return (*func[0], *(st for a in args for st in a[0])), ast.Call(func[1], [a[1] for a in args], [])

    def code_block(self, parameters: Tuple, statements: Tuple, return_value):
        if parameters and isinstance(parameters[-1][1], _varpar):
            parameters = ast.arguments([p[1] for p in parameters[:-1]], parameters[-1][1].content, [], [], None, [])
        else:
            parameters = ast.arguments([p[1] for p in parameters], None, [], [], None, [])
        statements = (*statements, ((*return_value[0], ast.Return(return_value[1])), None))
        statements = self.make_statements(statements)
        self._counter += 1
        return ((ast.FunctionDef(f"_{self._counter-1}", parameters, statements, []),),
                ast.Name(f"_{self._counter-1}", ast.Load()))

    def variadic_argument(self, name: str):
        return (), ast.Starred(ast.Name(name, ast.Load()), ast.Load())

    def list(self, content: Tuple):
        return tuple(st for c in content for st in c[0]), ast.List([c[1] for c in content], ast.Load())

    def file(self, statements: Tuple):
        return ast.fix_missing_locations(ast.Module(self.make_statements(statements)))

    def assignment(self, name: str, value):
        return (*value[0], ast.Assign([ast.Name(name, ast.Store())], value[1]),), None

    _counter = 0


def f_compile(text: str) -> ast.AST:
    return FLarkTransformer(FASTTransformer()).transform(f.parse(text))


from f.ast_compiler.builtins import f_globals

stdlib = f_compile(open(r"C:\Users\tramp\PycharmProjects\F\stdlib.f").read())
eval(compile(stdlib, "<test>", 'exec'), f_globals)
data = f_compile(open(r"C:\Users\tramp\PycharmProjects\F\test.f").read())
eval(compile(data, "<test>", 'exec'), f_globals)

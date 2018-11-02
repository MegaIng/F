import ast
from collections import namedtuple
from types import CodeType
from typing import Tuple, List, overload, TextIO, Dict, Any, Union
from warnings import warn

import f
from f.ast_compiler.builtins import f_globals
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
        assert name.startswith("...")
        if len(name) == 3:
            return (), _varpar(ast.arg(name, None))
        else:
            return (), _varpar(ast.arg(name[3:], None))

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

    def variadic_value(self, value):
        return value[0], ast.Starred(value[1], ast.Load())

    def list(self, content: Tuple):
        return tuple(st for c in content for st in c[0]), ast.List([c[1] for c in content], ast.Load())

    def file(self, statements: Tuple):
        return ast.fix_missing_locations(ast.Module(self.make_statements(statements)))

    def assignment(self, name: str, value):
        return (*value[0], ast.Assign([ast.Name(name, ast.Store())], value[1]),), ast.Name(name, ast.Load())

    _counter = 0


@overload
def f_compile(text: str, file_name: str = "<unknown>", debug=0) -> CodeType: raise NotImplementedError


@overload
def f_compile(file: TextIO, file_name: str = None, debug=0) -> CodeType: raise NotImplementedError


def f_compile(text, file_name=None, debug=0) -> CodeType:
    if file_name is None:
        try:
            file_name = text.name
        except AttributeError:
            file_name = "<unknwon>"
    try:
        text = text.read()
    except AttributeError:
        pass
    tree = f.parse(text)
    if debug > 0:
        from lark.tree import pydot__tree_to_png
        pydot__tree_to_png(tree, 'debug.png')
    tree = FLarkTransformer(FASTTransformer()).transform(tree)
    return compile(tree, file_name, 'exec', dont_inherit=False)


@overload
def f_eval(code: CodeType, argv: Tuple[str, ...] = None, f_locals: Dict[str, Any] = None, debug=0):
    raise NotImplementedError


@overload
def f_eval(code: Union[TextIO, str], argv: Tuple[str, ...] = None, f_locals: Dict[str, Any] = None,
           file_name: str = None, debug=0):
    raise NotImplementedError


def f_eval(code, argv=None, f_locals=None, file_name=None, debug=0):
    if not isinstance(code, CodeType):
        code = f_compile(code, file_name, debug - 1)
    elif file_name is not None:
        warn('`file_name` for already compiled code. `file_name` will be ignored.')
    if argv is None:
        argv = (file_name,)
    if debug:
        import uncompyle6
        uncompyle6.code_deparse(code)
        print()
    f_globals['...'] = argv
    eval(code, f_globals, f_locals)


f_eval(open(r"stdlib.f"))

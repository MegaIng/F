from argparse import ArgumentParser
from pathlib import Path

arg_parser = ArgumentParser('f')
arg_parser.add_argument('-m', '--mode', choices=('a', 'ast', 'i', 'interpreter', 'c', 'compiler'), default='a')

arg_parser.add_argument('program', nargs='?')
arg_parser.add_argument('argv', nargs='*')

n = arg_parser.parse_args()

if n.mode.startswith('c'):
    if not n.program:
        raise ValueError("Can not launch REPL with compiler")
    if n.argv:
        raise ValueError("Can not take argv for compiler")
    from f.c_compiler import f_compile

    with open("stdlib.f") as f:
        data = f.read() + "\n"
    with open(n.program) as f:
        data += f.read()
    f_compile(data, Path(n.program).with_suffix('.exe'))
else:
    if n.mode.startswith('i'):
        from f.interpreter import f_eval
    elif n.mode.startswith('a'):
        from f.ast_compiler import f_eval

    if n.program:
        with open(n.program) as f:
            data = f.read()
        f_eval(data, n.argv, debug=0)
    else:
        while True:
            f_eval(input("> "), debug=0)

from argparse import ArgumentParser

arg_parser = ArgumentParser('f')

arg_parser.add_argument('-i', '--interpreter', action='store_true',
                        help='Uses the interpreter instead of the ast-compiler')
arg_parser.add_argument('program', nargs='?')
arg_parser.add_argument('argv', nargs='*')

n = arg_parser.parse_args()

if n.interpreter:
    from f.interpreter import f_eval
else:
    from f.ast_compiler import f_eval

if n.program:
    with open(n.program) as f:
        data = f.read()
    f_eval(data, n.argv, debug=0)
else:
    while True:
        f_eval(input("> "), debug=0)

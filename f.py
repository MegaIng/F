from f_parser import parse

if __name__ == '__main__':
    import sys

    _,file, *argv = sys.argv
    code = parse(open(file).read())
    code.call(argv)

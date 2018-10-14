from f.interpreter import f_compile

if __name__ == '__main__':
    import sys

    _, file, *argv = sys.argv
    code = f_compile(open(file).read())
    code.call(argv)

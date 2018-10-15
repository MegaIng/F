from f.interpreter import f_eval

if __name__ == '__main__':
    import sys

    _, file, *argv = sys.argv
    f_eval(open(file).read(), (file, *argv))

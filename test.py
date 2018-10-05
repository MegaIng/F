from f import CodeBlock, FTransformer, Interpreter, f

tree: CodeBlock = FTransformer().transform(f.parse("""
foreach |x ({1 2 3}) y ({4 5 6})| [
    print x y    // prints 1 4; 2 5; 3 6
];
"""))
print(tree)
tree.call(())

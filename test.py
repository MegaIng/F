from f import CodeBlock, FTransformer, Interpreter, f

tree: CodeBlock = FTransformer().transform(f.parse("""
factorial := [|n|
    total := reference 1;
    i := reference n;
    until [!i = 0] [
        total <- (!total * !i);
        i <- (!i - 1)
    ];
    !total
];

until := [|condition action|
    while [not (condition ())] [
        do action
    ]
];
factorial 5;
"""))
print(tree.call(()))

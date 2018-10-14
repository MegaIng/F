# The Design Of F

September 2018

The last couple of weeks I thought a lot about this language idea.
Now it evolved far enough to show you my F language.
I called it F because that's the worst possible name I could think of quickly:
Single letter, ungoogleable, already taken.
This name allows me to focus on the important issues of language design
and not on bike-shedding.
Hopefully you will find the language inspiring in some way,
otherwise just enjoy your read!

In F there are no special forms like loops or conditionals.
All control flow happens via function application.
The syntax for applying a function is very simple, although slightly irregular:
A function with some arguments is just called as `func arg1 ... argN`;
a function with zero arguments is called as `func ()` with an empty pair
of parentheses. The reason for this is that functions are first-class values too,
so writing `func` without an empty pair of parentheses just represents the value
`func`.

```
functionWithArguments argument1 argument2 argument3;
functionWithoutArguments ();
```

The only two other elements of core syntax are variable definition and blocks.

A variable is defined as a value using the notation `variable := value`.
A block, lambda, anonymous function is enclosed by square brackets and
can either ignore its argument list or start with a block signature.

```
identityFunction := [|x| x ];
secondArg := [|x y| y ];
helloWorld := [ print "hello"; print "world" ];
```

For convenience, this introduction assumes literal syntax for lists
(`{a b c}`), strings (`"hello world"`), and numbers (`12.3`).

Some operators are also assumed, like `+` addition, but they are basically
just functions too.
This means the expressions `2 + 3` and `(+) 2 3` have the exact same meaning.
Like all other functions operators can also be variadic.

```
// Add two numbers with infix syntax
3 + 4;         // => 7

// Add two numbers without infix syntax
(+) 4 4;       // => 8

// Add more numbers without infix syntax
(+) 1 3 5;     // => 9
```

Special language level support for boolean logic are actually not needed.
`not` is just a function that inverts its argument,
`true` is a variable holding a true value by default,
`false` is a variable holding a false value by default,
and the variadic functions `any` and `all` respectively.

```
all true true false;  // => false
any true true false;  // => true
any false;            // => false
all true (not false); // => true
any ();               // => false
all ();               // => true
```

Any dyadic function can be used as infix by writing it between its arguments
with a colon after its name.

```
true and: true;       // => true
false and: not true;  // => false
or false false;       // => false
(1 = 1) or: (2 > 3);  // => true
```

The functions `and` and `or` do the exact same thing `all` and `any` do,
with the exception that they only take two arguments.
Also, the `and` and `or` functions apply blocks they receive to
zero arguments and treat the result as a boolean value.
That way short circuiting works.

```
true and: [ print "hello world"; false ];
  // => false (and does print)
false and: [ print "hello world"; false ];
  // => false (and does not print)
```

Control flow is also done using functions.
Take a look at the following code example.

```
factorial := [|n|
    if [n = 0] [
        1
    ] else [
        n * factorial (n - 1)
    ]
];
```

The conditional is just passing the `if` function 4 arguments:
the `[n = 0]` function, the `[1]` function,
the `else` function, and the `[n * factorial (n - 1)]` function.

If the first block evaluates to true, the `if` function just calls the second block
with no arguments, otherwise it applies the third block (`else`) to all of the
remaining arguments (`{[n * factorial (n - 1)]}`).

This means even more complex control flow is possible,
as the following example shows.

```
fibonacci := [|n|
    if [n = 1] [
        1
    ] else if [n = 2] [
        2
    ] else [
        fibonacci (n - 1) + fibonacci (n - 2)
    ]
];
```

Assuming a simple conditional function `either a b c` that just returns
`b` if `a` is true and `c` otherwise, the `if` function could be implemented
as follows. (Note: the `do` function applies its first argument to the rest
and is equivalent to Lisp's `funcall`)

```
if := [|condition action ...|
    do (either (condition ()) action [do ...])
];

else := [|...|
    do ...
];
```

Since F is a mostly functional language, immutable variables are the default
and actually the only thing provided.
This doesn't mean that it isn't possible to write imperative code though:
Like ML style languages F supports explicit references if that's desired,
so the factorial example from above can also be written as follows.

```
factorial := [|n|
    total := reference 1;
    i := reference n;
    while [!i > 0] [
        total <- !total * !i;
        i <- !i - 1
    ];
    !total
];
```

Note that `reference`, `(!)`, and `(<-)` are also just functions
and so is `while`.

The advantage of this style is an extreme amount of extensibility at no cost.

Say you'd rather phrase the factorial code above using an until-loop,
but your F system does not provide one. This is actually a non-issue,
as you can define it as a function yourself.

```
factorial := [|n|
    total := reference 1;
    i := reference n;
    until [!i = 0] [
        total <- !total * !i;
        i <- !i - 1
    ];
    !total
];

until := [|condition action|
    while [not (condition ())] [
        do action
    ]
];
```

This is really just the tip of the iceberg when it comes to extensibility.
You can even add do-while loops and more to the language.
Say we want to be able to write such a loop as `repeat/while`,
you can add the `repeat` feature in such a way, that `repeat/until`
becomes automatically available too.

```
repeat := [|action conditional ...|
    do action;
    do conditional ... action
];

// count down
count := reference 10;
repeat [
    print (!count);
    count <- !count - 1
] while [!count >= 0];

// count up
count <- 0;
repeat [
    count <- !count + 1;
    print (!count)
] until [!count = 10];
```

Since references in F are first-class it is actually possible to write
post-increment and such as functions too.

```
postModifier := [|fun|
    [|ref|
        value := !ref;
        ref <- fun (!ref);
        value ]
];

incr := postModifier [|x| x + 1];

// usage example
i := reference 5;
print (!i) (incr i) (!i); // prints 5 5 6
```

With your current knowledge of F, a lot of things are imaginable doing,
but some are still inconvenient. For example for/in loops are only hardly
expressible using the syntax we know so far.

```
foreach [|x| x + 1] xs;
```

This syntax is perfect for functional maps,
but most of the time you just want to place the function signature
in the actual argument position of the block and append the block
to the end of the whole function call. And in fact you can do exactly that.

```
foreach |x| xs [
    x + 1
];

// == foreach [|x| x + 1 ] xs
```

This syntax is also useful for expressing the whole `with-` family of Lisp macros.

```
withOpenFile |file| "my-file.txt" "w" [
    file writeLine: "First line...";
    file writeLine: "Some more lines...";
    file writeLine: "Last line."
];
```

An extension of this notation allows you to pass more arguments to the outer
function from within the argument list of the block by putting them in parentheses.

```
foreach |x ({1 2 3}) y ({4 5 6})| [
    print x y    // prints 1 4; 2 5; 3 6
];

// == foreach [|x y| print x y ] {1 2 3} {4 5 6}
```

This syntax can be used to express the `let` family of Lisp macros.

```
do |x (5) y (10)| [ x + y ]; // => 15
// == do [|x y| x + y ] 5 10
```

My intention for this design is to create a practical and minimal
programming language.

I am looking forward to write more about F in the future,
but I probably won't implement it (not that good of a programmer actually),
however if you want to write an interpreter or compiler for an F dialect,
feel free to do so, just let me know!
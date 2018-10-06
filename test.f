preModifier := [|fun|
    [|ref|
        ref <- fun (!ref);
        !ref ]
];
postModifier := [|fun|
    [|ref|
        value := !ref;
        ref <- fun (!ref);
        value ]
];

postIncr := postModifier [|x| x + 1];
preIncr := preModifier [|x| x + 1];

// usage example
i := reference 5;
print (!i) (postIncr i) (!i); // prints 5 5 6
i <- 5;
print (!i) (preIncr i) (!i); // prints 5 6 6

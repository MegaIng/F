factorial := [|n|
    total := reference 1;
    i := reference n;
    while [!i > 0] [
        total <- !total * !i;
        i <- !i - 1
    ];
    !total
];
print (factorial 4);
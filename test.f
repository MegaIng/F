// Examples from README.md

//do [
//  functionWithArguments argument1 argument2 argument3;
//  functionWithoutArguments ();
//];
do [
  identityFunction := [|x| x ];
  secondArg := [|x y| y ];
  helloWorld := [ print "hello"; print "world" ];
];
do [
  // Add two numbers with infix syntax
  3 + 4;         // => 7

  // Add two numbers without infix syntax
  (+) 4 4;       // => 8

  // Add more numbers without infix syntax
  (+) 1 3 5;     // => 9
];
do [
  all true true false;  // => false
  any true true false;  // => true
  any false;            // => false
  all true (not false); // => true
  any ();               // => false
  all ();               // => true
];
do [
  true and: true;       // => true
  false and: not true;  // => false
  or false false;       // => false
  (1 = 1) or: (2 > 3);  // => true
];
do [
  true and: [ print "hello world"; false ];
    // => false (and does print)
  false and: [ print "hello world"; false ];
    // => false (and does not print)
];
do [
  factorial := [|n|
      if [n = 0] [
          1
      ] else [
          n * factorial (n - 1)
      ]
  ];
];
do [
  fibonacci := [|n|
      if [n = 1] [
          1
      ] else if [n = 2] [
          2
      ] else [
          fibonacci (n - 1) + fibonacci (n - 2)
      ]
  ];
];
do [
  if := [|condition action ...|
      do (either (condition ()) action [do ...])
  ];

  else := [|...|
      do ...
  ];
];
do [
  factorial := [|n|
      total := reference 1;
      i := reference n;
      while [!i > 0] [
          total <- !total * !i;
          i <- !i - 1
      ];
      !total
  ];
];
do [
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
];
do [
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
];
do [
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
];
do [
  xs := {1 2 3};
  foreach [|x| x + 1] xs;
];
do [
  xs := {1 2 3};
  foreach |x| xs [
      x + 1
  ];

  // == foreach [|x| x + 1 ] xs
];
do [
  withOpenFile |file| "my-file.txt" "w" [
      file writeLine: "First line...";
      file writeLine: "Some more lines...";
      file writeLine: "Last line."
  ];
];
do [
  foreach |x ({1 2 3}) y ({4 5 6})| [
      print x y    // prints 1 4; 2 5; 3 6
  ];

  // == foreach [|x y| print x y ] {1 2 3} {4 5 6}
];
do [
  do |x (5) y (10)| [ x + y ]; // => 15
  // == do [|x y| x + y ] 5 10
];
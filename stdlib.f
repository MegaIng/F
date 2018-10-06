until := [|condition action|
    while [not (condition ())] [
        do action
    ]
];

if := [|condition action ...|
    do (either (condition ()) action [do ...])
];

else := [|...|
    do ...
];

repeat := [|action conditional ...|
    do action;
    do conditional ... action
];

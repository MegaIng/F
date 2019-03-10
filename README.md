# F
An Implementation of F by @ac1235 (https://ac1235.github.io/f.html)

## Implementation Details

* Syntax completely like in the documentation by @ac1235 (All of his example can be parsed and executed)
* Numbers are always the `Decimal` type from python.
* Strings have (almost) C-like escaping and are written between `"`
* Variadic Value Syntax, allowing for List unpacking (`...(<List-Value>)`)

## How to use

* install the latest version of [python 3 (at least 3.7)](https://www.python.org/downloads/)
* execute `pip install lark-parser`

### `f.py`
 
 `f [-h] [-m {a,i,c}] [program] argv*`
 
 * `program` selects the file to be run. If not present, will start a REPL.
 * `-m`/`--mode` selects a mode on ho to handle the input
   * `a`/`ast` chooses the to ast compiler. The default
   * `i`/`interpreter` chooses the interpreter. The slowest option. Should get extended with a debugger
   * `c`/`compiler` chooses the to C compiler. Can not run a REPL or take argvs, but generates a executable (currently only on windows correctly)

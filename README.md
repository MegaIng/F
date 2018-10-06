# F
An Implementation of F by @ac1235 (https://ac1235.github.io/f.html)

## Implementation Details

* Syntax completly like in the documentation by @ac1235 (All of his example can be parsed)
  * Wrong scoping (He uses lexical scoping, Currently implemented is dynamic scoping) (Will be changed)
* Many functions are missing (as example the `with*` family)
* Numbers are always the `Decimal` type from python.
* Strings have simple escaping (will be changed) and are written between `"`
* Many fundamental functions are missing (Many, many (No list access as example))

## How to use

* install the latest version of [python 3 (at least 3.7)](https://www.python.org/downloads/)
* run `pip install lark-parser`
* execute `test.py` via python
  * code changes have to be done manualy inside `test.py` at the moment

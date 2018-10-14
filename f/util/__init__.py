from typing import re

escaped_values = {
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
    "\\": "\\",
    "\'": "\'",
    "\"": "\"",
    "\n": ""
}


def unescape_string(data: str) -> str:
    return re.sub(r'\\(.)', lambda m: escaped_values.get(m.group(1), m.group(1)), data)

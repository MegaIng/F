import re

from f.interpreter import f_compile

with open("f/grammar/f.md") as file:
    data = file.read()

for example in re.finditer("```\n(.*?)\n```", data, re.DOTALL):
    example = example.group(1) + "\n"
    print(example)
    print(f_compile(example))
    try:
        f_compile(example).call((), True)
    except NameError as e:
        print("NameError", e)
    print("-" * 100)
    input("")

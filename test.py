import sys

from f import CodeBlock, parse
import re

with open("f.md") as file:
    data = file.read()

for example in re.finditer("```\n(.*?)\n```",data,re.DOTALL):
    example = example.group(1)+"\n"
    print(example)
    print(parse(example))
    try:
        parse(example).call((),True)
    except NameError as e:
        print("NameError",e)
    print("-"*100)
    input("")
# print(tree)
# tree.call(())

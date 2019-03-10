from typing import List, Type

from . import gcc
from .base import AbstractCCompiler

_available_compilers: List[Type[AbstractCCompiler]] = [sbcls for sbcls in AbstractCCompiler.__subclasses__()
                                                       if sbcls.is_available()]


def get_compiler(name: str = None) -> AbstractCCompiler:
    if len(_available_compilers) == 0:
        raise ValueError("Couldn't find any compiler for your system. If you have one installed,"
                         " please send a ticket, so we can added it.")
    if name is not None:
        for cls in _available_compilers:
            if cls.name == name:
                return cls()
        raise ValueError("Couldn't find a compiler matching the specified name.")
    else:
        return _available_compilers[0]()

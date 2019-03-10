from __future__ import annotations

import platform
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Type


@dataclass
class CompilationError(Exception):
    compiler: str
    return_code: int
    file: Path
    cmd: List[str]
    data: str

    def __post_init__(self):
        super(CompilationError, self).__init__(f"{self.compiler} failed with return code {self.return_code}"
                                               f" while compiling {str(self.file)!r}:\n"
                                               f"Raw commandline:{' '.join(self.cmd)}\n\n{self.data}")


@dataclass
class CompilationOptions:
    pass


class AbstractCCompiler(ABC):
    name: str

    @abstractmethod
    def compile_to_executable(self, file: Path, out: Path = None, options: CompilationOptions = None):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def is_available(cls):
        raise NotImplementedError

    if TYPE_CHECKING:
        @classmethod
        def __subclasses__(cls) -> List[Type[AbstractCCompiler]]: ...


def make_executable_path(path: Path) -> Path:
    if platform.system() == "Windows":
        return path.with_suffix(".exe")
    elif platform.system() == "Linux":
        if '.' not in path.name:
            return path
        return path.with_name(path.name.rpartition('.')[-1])
    else:
        raise ValueError(f"Unknown platform '{platform.system()}'")

import subprocess
from pathlib import Path

from general_c_compiler.base import CompilationOptions, AbstractCCompiler, make_executable_path, CompilationError


class GCCCompiler(AbstractCCompiler):
    name: str = 'gcc'

    def compile_to_executable(self, file: Path, out: Path = None, options: CompilationOptions = None):
        assert options is None
        file = file.resolve()
        out = make_executable_path(file if out is None else out).resolve()
        cmd = ["gcc", "-o", str(out), str(file)]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise CompilationError(self.name, result.returncode, file, cmd, result.stderr)

    @classmethod
    def is_available(cls):
        try:
            result = subprocess.run(["gcc", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return result.returncode == 0
        except FileNotFoundError:
            return False

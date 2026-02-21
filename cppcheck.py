#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path
import subprocess

from fastwalk import walk_files


def validate_cpp(path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["clang++", "-fsyntax-only", str(path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True, ""
    return False, proc.stderr


if __name__ == "__main__":
    dir = Path().cwd()
    for pth in walk_files(dir):
        path = Path(pth)
        if path.is_file() and path.suffix in {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}:
            if not validate_cpp(path):
                print(f"[\u2716] : {path.name}")
            else:
                print(f"[\u2705] : {path.name}")

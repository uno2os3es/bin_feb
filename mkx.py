#!/usr/bin/env python3
from pathlib import Path
import stat


def has_shebang(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            first_three = f.read(3)
            return first_three == b"#!/"
    except (OSError, PermissionError):
        return False


def make_executable(path: Path) -> None:
    current_mode = path.stat().st_mode
    executable_bits = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    new_mode = current_mode | executable_bits
    path.chmod(new_mode)


def process_directory(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if has_shebang(path):
            mode = path.stat().st_mode
            if not (mode & stat.S_IXUSR):
                make_executable(path)
                print(f"[+] Made executable: {path}")
            else:
                print(f"[=] Already executable: {path}")


if __name__ == "__main__":
    process_directory(Path.cwd())

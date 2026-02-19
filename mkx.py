#!/usr/bin/env python3
import os
import stat
from pathlib import Path


def has_shebang(path: Path) -> bool:
    """
    Return True if file starts with a shebang (#!).
    """
    try:
        with path.open("rb") as f:
            first_two = f.read(2)
            return first_two == b"#!"
    except (OSError, PermissionError):
        return False


def make_executable(path: Path) -> None:
    """
    Add executable bits (user/group/other) while preserving existing perms.
    """
    current_mode = path.stat().st_mode
    executable_bits = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    new_mode = current_mode | executable_bits
    path.chmod(new_mode)


def process_directory(root: Path) -> None:
    """
    Recursively process files in root directory.
    """
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

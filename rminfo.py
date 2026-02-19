#!/data/data/com.termux/files/usr/bin/env python3
"""Remove author metadata header from python files (with or without extension)."""

import os
from pathlib import Path

from fastwalk import walk_files


def is_python_file(path: str) -> bool:
    """Detect python files even without extension."""
    if os.path.isdir(path):
        return False

    if path.suffix == ".py":
        return True

    try:
        with open(
            path,
            encoding="utf-8",
            errors="ignore",
        ) as f:
            first = f.readline().strip()
            if first.startswith("#!") and "python" in first:
                return True
            sample = f.read(200)
            return any(
                tok in sample
                for tok in (
                    "def ",
                    "class ",
                    "import ",
                    "from ",
                )
            )
    except Exception:
        return False


def remove_header(path) -> None:
    original = []
    cleaned = []
    try:
        with open(
            path,
            encoding="utf-8",
            errors="ignore",
        ) as f:
            original = f.readlines()
    except Exception:
        return

    for line in original:
        if not (line.startswith("# Author ") or line.startswith("# Email ") or line.startswith("# Time ")):
            cleaned.append(line)
    print(f"{len(original)}=={len(cleaned)}")
    if cleaned != original:
        ans = "y"
        if ans == "y":
            with open(path, "w", encoding="utf-8") as fo:
                fo.write("".join(cleaned))


def main() -> None:
    for pth in walk_files("."):
        path = Path(pth)
        if is_python_file(path):
            remove_header(path)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
python_formatter.py
Requirements: pip install yapf black autopep8 isort autoflake
"""

from __future__ import annotations

import argparse
from collections import deque
import contextlib
from multiprocessing import Pool
from pathlib import Path
from time import perf_counter

from fastwalk import walk_files

MAX_IN_FLIGHT = 16

# Standard library imports remain at top
IGNORED_DIRS = {
    ".git",
    "dist",
    "build",
    "__pycache__",
}

# ---------- UTILS ----------


def is_python_file(path: Path) -> bool:
    if path.suffix in {".py", ".pyi", ".pyx"}:
        return True
    try:
        with path.open("rb") as f:
            line = f.readline(100)
            return line.startswith(b"#!") and b"python" in line.lower()
    except Exception:
        return False


# ---------- FORMATTING LOGIC ----------


def format_single_file(file: Path, args) -> bool:
    """Core formatting logic using Lazy Imports."""
    try:
        original_code = file.read_text(encoding="utf-8")
        code = original_code

        # 1. Remove Unused Imports/Variables
        if args.remove_all_unused_imports:
            import autoflake

            code = autoflake.fix_code(
                code,
                remove_all_unused_imports=True,
                ignore_init_module_imports=True,
            )

        # 2. Sort Imports
        if args.isort:
            import isort

            code = isort.code(code)

        # 3. Code Style Formatting
        if args.black:
            import black

            with contextlib.suppress(black.NothingChanged):
                code = black.format_str(code, mode=black.Mode(line_length=120))
        elif args.autopep:
            import autopep8

            code = autopep8.fix_code(code, options={"aggressive": 2})
        else:
            # Lazy import for yapf
            from yapf.yapflib import yapf_api

            code, _ = yapf_api.FormatCode(code)

        # 4. Write back only if changed
        if len(code) != len(original_code):
            file.write_text(code, encoding="utf-8")
            print(f"[OK]  {file.name}")
            return True
        else:
            print(f"[NO CHNGE]  {file.name}")
            return False
    except Exception as e:
        print(f"[ERROR]  {file.name}: {e}")
        return False


# ---------- EXECUTION ----------


def main() -> None:
    p = argparse.ArgumentParser(description="Fast Python API-based formatter (Lazy Loading)")
    p.add_argument(
        "-b",
        "--black",
        action="store_true",
        help="Use black style",
    )
    p.add_argument(
        "-a",
        "--autopep",
        action="store_true",
        help="Use autopep8 style",
    )
    p.add_argument(
        "-i",
        "--isort",
        action="store_true",
        help="Sort imports",
    )
    p.add_argument(
        "-r",
        "--remove-all-unused-imports",
        action="store_true",
        help="Autoflake cleanup",
    )
    args = p.parse_args()

    start_time = perf_counter()

    files = []
    for pth in walk_files("."):
        path = Path(pth)
        if (
            path.is_file()
            and not any(part in IGNORED_DIRS for part in path.parts)
            and is_python_file(path)
            and not path.is_symlink()
        ):
            files.append(path)

    if not files:
        print("No Python files detected.")
        return

    print(f"Formatting {len(files)} files...")

    with Pool(8) as p:
        pending = deque()
        for name in files:
            pending.append(
                p.apply_async(
                    format_single_file,
                    (
                        (name),
                        (args),
                    ),
                )
            )
            if len(pending) >= MAX_IN_FLIGHT:
                pending.popleft().get()
        while pending:
            pending.popleft().get()

    duration = perf_counter() - start_time
    print(f"Total Runtime: {duration:.4f} seconds")


if __name__ == "__main__":
    main()

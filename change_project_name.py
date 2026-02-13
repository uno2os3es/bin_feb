#!/data/data/com.termux/files/usr/bin/env python3
"""Recursively replace text in file contents AND in file/folder names.

Usage:
    change_project_nsme <text_to_change> <replacement_text>

use case:
    when u wanna upload a pkg to pypi and got this medsage:
        u are not allowed to upload to this project
        meaning:
             nzme slready taken
             project with this name exist and
             u should choose a new one
             so this script comes useful

Example:
             chsnge_project_name fileutils pyfileutils

             at the end rename parent folder manually
             always run this inside project folder

"""

import os
import shutil
import sys


def replace_in_file(path: str, old: str, new: str) -> None:
    """Why: update file content safely."""
    try:
        with open(
                path,
                encoding="utf-8",
                errors="ignore",
        ) as f:
            text = f.read()
    except (UnicodeDecodeError, PermissionError):
        return

    if old not in text:
        return

    new_text = text.replace(old, new)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)


def rename_path(path: str, old: str, new: str) -> str:
    """Why: rename files/folders containing old name."""
    dirname = os.path.dirname(path)
    basename = os.path.basename(path)

    if old not in basename:
        return path

    new_basename = basename.replace(old, new)
    new_path = os.path.join(dirname, new_basename)
    if os.path.exists(new_path):
        print(f"path by name {new_path} already exists\n rename it manually")
        return path

    try:
        shutil.move(path, new_path)
        return new_path
    except Exception:
        return path


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <text_to_change> <replacement_text>")
        sys.exit(1)

    old = sys.argv[1]
    new = sys.argv[2]

    # Phase 1: replace contents in all files
    for root, _, files in os.walk(".", topdown=True):
        for fn in files:
            replace_in_file(os.path.join(root, fn), old, new)

    # Phase 2: rename files & folders bottom-up
    for root, dirs, files in os.walk(".", topdown=False):
        for fn in files:
            rename_path(os.path.join(root, fn), old, new)

        for dn in dirs:
            rename_path(os.path.join(root, dn), old, new)


if __name__ == "__main__":
    main()

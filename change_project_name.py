#!/data/data/com.termux/files/usr/bin/env python3
import os
import shutil
import sys


def replace_in_file(path: str, old: str, new: str) -> None:
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
    for root, _, files in os.walk(".", topdown=True):
        for fn in files:
            replace_in_file(os.path.join(root, fn), old, new)
    for root, dirs, files in os.walk(".", topdown=False):
        for fn in files:
            rename_path(os.path.join(root, fn), old, new)
        for dn in dirs:
            rename_path(os.path.join(root, dn), old, new)


if __name__ == "__main__":
    main()

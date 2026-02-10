#!/data/data/com.termux/files/usr/bin/python
import os

import regex as re


from fastwalk import walk_files
from pathlib import Path


from deep_translator import GoogleTranslator

# Directory to scan
DIRECTORY = "."

# Detect non-ASCII characters (Chinese, Japanese, Korean, Arabic, etc.)
non_english_pattern = re.compile(r"[^\x00-\x7F]")


def translate_if_needed(name: str) -> str:
    """Translate filename only if it contains non-English characters."""
    base, ext = os.path.splitext(name)

    # Skip if already English
    if not non_english_pattern.search(base):
        return name

    try:
        translated = GoogleTranslator(source="auto", target="en").translate(base)
        return translated + ext
    except Exception as e:
        print(f"Translation error for '{name}': {e}")
        return name


def get_unique_path(path: Path) -> Path:
    """Generate a unique non-conflicting path by adding _1, _2, etc."""
    if not path.exists():
        return path

    base = path.stem
    ext = path.suffix
    parent = path.parent

    counter = 1
    while True:
        new_path = parent / f"{base}_{counter}{ext}"
        if not new_path.exists():
            return new_path
        counter += 1


def rename_files(directory: str):
    for pth in walk_files(directory):
        path = Path(filepath)

        # Handle files
        if path.is_file():
            new_name = translate_if_needed(path.name)

            # Skip if no change
            if new_name == path.name:
                continue

            new_path = path.parent / new_name
            new_path = get_unique_path(new_path)

            os.rename(path, new_path)
            print(f"File renamed: {path.name} -> {new_path.name}")

        # Handle directories
        elif path.is_dir():
            new_name = translate_if_needed(path.name)

            # Skip if no change
            if new_name == path.name:
                continue

            new_path = path.parent / new_name
            new_path = get_unique_path(new_path)

            os.rename(path, new_path)
            print(f"Directory renamed: {path.name} -> {new_path.name}")


if __name__ == "__main__":
    rename_files(DIRECTORY)

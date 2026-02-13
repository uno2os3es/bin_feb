#!/data/data/com.termux/files/usr/bin/python
import os
from pathlib import Path

import regex as re
from deep_translator import GoogleTranslator
from fastwalk import walk_files

DIRECTORY = "."

# Detect non‑ASCII characters
non_english_pattern = re.compile(r"[^\x00-\x7F]")


def is_english(text):
    """Return True if filename contains only ASCII characters."""
    return not non_english_pattern.search(text)


def translate_filename(filename):
    """Translate non-English filename to English."""
    name, ext = os.path.splitext(filename)
    try:
        translated = GoogleTranslator(source="auto",
                                      target="en").translate(name)
        return translated + ext
    except Exception as e:
        print(f"Translation error for {filename}: {e}")
        return filename


def rename_files(directory):

    for pth in walk_files(directory):
        path = Path(pth)

        # Skip already-English names
        if is_english(path.name):
            continue

        # --- FILES ---
        if path.is_file():
            original_path = path
            new_name = translate_filename(path.name)
            new_path = path.with_name(new_name)

            counter = 1
            while new_path.exists():
                name, ext = os.path.splitext(new_name)
                new_path = path.with_name(f"{name}_{counter}{ext}")
                counter += 1

            os.rename(original_path, new_path)
            print(f"Renamed file: {original_path.name} -> {new_path.name}")

        # --- DIRECTORIES ---
        elif path.is_dir():
            original_path = path
            new_name = translate_filename(path.name)
            new_path = path.with_name(new_name)

            counter = 1
            while new_path.exists():
                new_path = Path(f"{original_path}_{counter}")
                counter += 1

            os.rename(original_path, new_path)
            print(
                f"Renamed directory: {original_path.name} -> {new_path.name}")


if __name__ == "__main__":
    rename_files(DIRECTORY)

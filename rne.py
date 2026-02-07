#!/data/data/com.termux/files/usr/bin/python
import os
from pathlib import Path

import regex as re
import rignore
from deep_translator import GoogleTranslator

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
        translated = GoogleTranslator(source="auto", target="en").translate(name)
        return translated + ext
    except Exception as e:
        print(f"Translation error for {filename}: {e}")
        return filename


def rename_files(directory):
    for filepath in rignore.walk(directory):
        fp = Path(filepath)

        # Skip root directory
        if fp.name == ".":
            continue

        # Skip already-English names
        if is_english(fp.name):
            continue

        # --- FILES ---
        if fp.is_file():
            original_fp = fp
            new_name = translate_filename(fp.name)
            new_fp = fp.with_name(new_name)

            counter = 1
            while new_fp.exists():
                name, ext = os.path.splitext(new_name)
                new_fp = fp.with_name(f"{name}_{counter}{ext}")
                counter += 1

            os.rename(original_fp, new_fp)
            print(f"Renamed file: {original_fp.name} -> {new_fp.name}")

        # --- DIRECTORIES ---
        elif fp.is_dir():
            original_fp = fp
            new_name = translate_filename(fp.name)
            new_fp = fp.with_name(new_name)

            counter = 1
            while new_fp.exists():
                new_fp = Path(f"{original_fp}_{counter}")
                counter += 1

            os.rename(original_fp, new_fp)
            print(f"Renamed directory: {original_fp.name} -> {new_fp.name}")


if __name__ == "__main__":
    rename_files(DIRECTORY)

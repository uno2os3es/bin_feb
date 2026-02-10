#!/data/data/com.termux/files/usr/bin/python
import os
from pathlib import Path
import sys

from deep_translator import GoogleTranslator
from fastwalk import walk_files
import regex as re

# Directory containing your files
DIRECTORY = "."
CHUNK_SIZE = 2000  # words per translation chunk
TARGET_LANGUAGE = "en"  # Translate to English

# Regex to detect non-ASCII characters (East Asian scripts)
non_english_pattern = re.compile(r"[^\x00-\x7F]")


def chunk_text(text, chunk_size=CHUNK_SIZE):
    """Split text into chunks of approx chunk_size words."""
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i : i + chunk_size])


def translate_text(text):
    """Translate text using deep-translator."""
    try:
        return GoogleTranslator(source="auto", target=TARGET_LANGUAGE).translate(text)
    except Exception as e:
        print(f"Error translating text chunk: {e}")
        return text


def translate_file(filepath):
    """Translate the contents of a single file in chunks."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    if not non_english_pattern.search(content):
        print(f"No non-English content found in {filepath}, skipping.")
        return

    translated_chunks = []
    for chunk in chunk_text(content):
        translated_chunk = translate_text(chunk)
        translated_chunks.append(translated_chunk)

    translated_content = "\n\n".join(translated_chunks)

    new_filepath = os.path.join(
        os.path.dirname(filepath),
        f"translated_{os.path.basename(filepath)}",
    )
    with open(new_filepath, "w", encoding="utf-8") as f:
        f.write(translated_content)

    print(f"saved as {new_filepath}")


def translate_folder(directory):
    for pth in walk_files(directory):
        path = Path(pth)
        if path.is_file():
            translate_file(path)


if __name__ == "__main__":
    choice = input("translate a f)ile or d)ir?")
    if choice == "d":
        translate_folder(DIRECTORY)
    elif choice == "f":
        fn = input("filename:").strip()
        translate_file(fn)
    else:
        print("enter d for dir and f for file.")
        sys.exit(1)

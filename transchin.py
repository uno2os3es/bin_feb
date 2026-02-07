#!/data/data/com.termux/files/usr/bin/python

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from deep_translator import GoogleTranslator
import regex as re
import rignore

DIRECTORY = "."
CHUNK_SIZE = 2000  # characters per chunk (safe for Google Translate)

# Detect non-ASCII characters
non_english_pattern = re.compile(r"[^\x00-\x7F]")


def is_text_file(path: Path) -> bool:
    """Check if file is likely text (not binary)."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(2048)
        return b"\x00" not in chunk
    except OSError:
        return False


def split_into_chunks(text: str, size: int):
    """Split text into safe translation chunks."""
    return [text[i : i + size] for i in range(0, len(text), size)]


def translate_chunk(chunk: str) -> str:
    """Translate a single chunk."""
    try:
        return GoogleTranslator(source="auto", target="en").translate(chunk)
    except Exception as e:
        print(f"Chunk translation error: {e}")
        return chunk


def translate_file(path: Path):
    """Translate file contents in parallel and save to fname_eng.ext."""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except:
        print(f"Skipping unreadable file: {path}")
        return

    # Skip if already English
    if not non_english_pattern.search(content):
        return

    # Split into chunks
    chunks = split_into_chunks(content, CHUNK_SIZE)

    # Translate in parallel
    with ThreadPoolExecutor(max_workers=8) as executor:
        translated_chunks = list(executor.map(translate_chunk, chunks))

    translated_text = "".join(translated_chunks)

    # Output file: fname_eng.ext
    new_name = f"{path.stem}_eng{path.suffix}"
    new_path = path.parent / new_name

    try:
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(translated_text)
        print(f"Translated → {new_path.name}")
    except Exception as e:
        print(f"Error writing {new_path}: {e}")


def process_directory(directory: str):
    for filepath in rignore.walk(directory):
        fp = Path(filepath)

        if fp.is_file() and is_text_file(fp):
            translate_file(fp)


if __name__ == "__main__":
    process_directory(DIRECTORY)

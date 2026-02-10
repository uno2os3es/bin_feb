#!/data/data/com.termux/files/usr/bin/python
from concurrent.futures import ThreadPoolExecutor, as_completed

import regex as re
from deep_translator import GoogleTranslator
from fastwalk import walk_files
from pathlib import Path

# Directory to scan
DIRECTORY = "."

# Characters per translation chunk
CHUNK_SIZE = 2000

# Detect non-ASCII characters
non_english_pattern = re.compile(r"[^\x00-\x7F]")


def is_text_file(path: Path) -> bool:
    """Check if file is likely text (not binary)."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(2048)
        return b"\x00" not in chunk
    except:
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

    chunks = split_into_chunks(content, CHUNK_SIZE)

    # Translate chunks in parallel
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
    """Process all files in parallel."""
    files = []

    # Collect eligible files
    for pth in walk_files(directory):
        path = Path(pth)
        if path.is_file() and is_text_file(path):
            files.append(path)

    print(f"Found {len(files)} text files to process")

    # Process files in parallel
    with ThreadPoolExecutor(8) as executor:
        futures = {executor.submit(translate_file, f): f for f in files}

        for future in as_completed(futures):
            f = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error processing {f}: {e}")


if __name__ == "__main__":
    process_directory(DIRECTORY)

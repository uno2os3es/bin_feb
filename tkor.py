#!/data/data/com.termux/files/usr/bin/env python3
"""Translate a text file from Korean → English using deep-translator,
reading in chunks to avoid API limits.

Usage:
    python translate.py input.py -g mygame
"""

import argparse
from pathlib import Path
import sys

from deep_translator import GoogleTranslator

CHUNK_SIZE = 2000  # limit chunk size for translation API


def read_text_file(path: Path) -> str:
    """Read UTF-8 text file; supports text-based extensions only."""
    allowed = {
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".py",
    }
    ext = path.suffix.lower()
    if ext not in allowed:
        raise ValueError(f"Unsupported file type: {ext}")
    return path.read_text(encoding="utf-8")


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks. Required for API limits."""
    return [text[i : i + size] for i in range(0, len(text), size)]


def translate_chunks(chunks: list[str]) -> str:
    """Translate chunks sequentially and accumulate result."""
    translator = GoogleTranslator(source="ko", target="en")
    translated_parts = []

    for chunk in chunks:
        # why: API may fail on long strings; chunking prevents errors.
        translated_parts.append(translator.translate(chunk))

    return "".join(translated_parts)


def write_text_file(path: Path, data: str) -> None:
    """Write UTF-8 text file."""
    path.write_text(data, encoding="utf-8")


def build_output_path(input_path: Path) -> Path:
    """Return output path `<filename>_eng.<ext>`."""
    return input_path.with_name(f"{input_path.stem}_eng{input_path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate Korean → English using chunked deep-translator.")
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to input file.",
    )
    parser.add_argument(
        "-g",
        "--game",
        type=str,
        default=None,
        help="Optional game argument.",
    )
    args = parser.parse_args()

    in_path = Path(args.input_path)

    if not in_path.exists():
        print(
            f"Error: File not found: {in_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        original_text = read_text_file(in_path)
    except Exception as exc:
        print(f"Read error: {exc}", file=sys.stderr)
        sys.exit(1)

    chunks = chunk_text(original_text)

    try:
        translated_text = translate_chunks(chunks)
    except Exception as exc:
        print(
            f"Translation error: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    out_path = build_output_path(in_path)

    try:
        write_text_file(out_path, translated_text)
    except Exception as exc:
        print(f"Write error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Saved translated file → {out_path}")


if __name__ == "__main__":
    main()

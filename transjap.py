#!/data/data/com.termux/files/usr/bin/env python3
"""Translate a text file from jap → English using deep-translator.

Usage:
    python translate.py input.txt -g mygame
"""

import argparse
import sys
from pathlib import Path

from deep_translator import GoogleTranslator


def read_text_file(path: Path) -> str:
    """Read UTF-8 text file. Raises error for non-text extensions."""
    allowed = {
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".py",
        "",
    }
    if path.suffix.lower() not in allowed:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    return path.read_text(encoding="utf-8")


def write_text_file(path: Path, data: str) -> None:
    """Write UTF-8 text file."""
    path.write_text(data, encoding="utf-8")


def translate_text(text: str) -> str:
    """Translate japan text to English. External API call."""
    translator = GoogleTranslator(source="ja", target="en")
    return translator.translate(text)


def build_output_path(input_path: Path) -> Path:
    """Return `<filename>_eng.<ext>` in the same directory."""
    return input_path.with_name(f"{input_path.stem}_eng{input_path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Translate jap → English using deep-translator.")
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to input text file.",
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

    try:
        translated = translate_text(original_text)
    except Exception as exc:
        print(
            f"Translation error: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    out_path = build_output_path(in_path)

    try:
        write_text_file(out_path, translated)
    except Exception as exc:
        print(f"Write error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Saved translated file → {out_path}")


if __name__ == "__main__":
    main()

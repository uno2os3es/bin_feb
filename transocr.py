#!/data/data/com.termux/files/usr/bin/env python3
"""
- Auto language detection
- OCR for JPG/PNG
- Image preprocessing for better OCR accuracy
- Saves raw OCR text separately
- Chunked translation to avoid API limits.
"""

import argparse
import sys
from pathlib import Path

import pytesseract
from deep_translator import GoogleTranslator
from langdetect import DetectorFactory, detect
from PIL import Image, ImageEnhance, ImageFilter

# Ensures consistent results from langdetect
DetectorFactory.seed = 0
TEXT_EXT = {".txt", ".md", ".csv", ".json", ".py"}
IMAGE_EXT = {".jpg", ".jpeg", ".png"}
CHUNK_SIZE = 2000

# -------------------------------
# Language detection
# -------------------------------


def detect_lang_from_text(text: str) -> str:
    if not text.strip():
        return "unknown"
    try:
        return detect(text[:500])
    except Exception:
        return "unknown"


# -------------------------------
# Text file handling
# -------------------------------


def read_text_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext not in TEXT_EXT:
        msg = f"Unsupported text file: {ext}"
        raise ValueError(msg)
    return path.read_text(encoding="utf-8")


# -------------------------------
# OCR + Image Processing
# -------------------------------


def preprocess_image(
    img: Image.Image,
) -> Image.Image:
    """Improve OCR accuracy by cleaning the image."""
    # Convert to grayscale
    img = img.convert("L")
    # Increase contrast
    img = ImageEnhance.Contrast(img).enhance(2.0)
    # Apply threshold
    img = img.point(lambda x: 0 if x < 160 else 255)
    # Reduce noise
    return img.filter(ImageFilter.MedianFilter(size=3))


def read_image_ocr(path: Path) -> str:
    """Extract text from image using OCR with preprocessing."""
    try:
        img = Image.open(path)
        img = preprocess_image(img)
        return pytesseract.image_to_string(img)
    except Exception as e:
        msg = f"OCR failed: {e}"
        raise RuntimeError(msg)


# -------------------------------
# Translation
# -------------------------------


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list:
    return [text[i : i + size] for i in range(0, len(text), size)]


def translate_chunks(chunks, src_lang: str) -> str:
    translator = GoogleTranslator(source=src_lang, target="en")
    output = [translator.translate(chunk) for chunk in chunks]
    return "".join(output)


# -------------------------------
# Output builders
# -------------------------------


def build_translated_output_path(
    input_path: Path,
) -> Path:
    if input_path.suffix.lower() in IMAGE_EXT:
        return input_path.with_name(f"{input_path.stem}_eng.txt")
    return input_path.with_name(f"{input_path.stem}_eng{input_path.suffix}")


def build_raw_ocr_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_ocr.txt")


# -------------------------------
# Main
# -------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate text or image to English.")
    parser.add_argument("input_path")
    parser.add_argument(
        "--lang",
        default="auto",
        help="Source language code or 'auto'",
    )
    args = parser.parse_args()
    in_path = Path(args.input_path)
    if not in_path.exists():
        sys.exit(1)
    # Read input
    try:
        if in_path.suffix.lower() in TEXT_EXT:
            text = read_text_file(in_path)
        elif in_path.suffix.lower() in IMAGE_EXT:
            text = read_image_ocr(in_path)
            # Always save raw OCR output
            raw_ocr_path = build_raw_ocr_path(in_path)
            raw_ocr_path.write_text(text, encoding="utf-8")
        else:
            msg = "Unsupported file type. Use text, jpg, jpeg, png."
            raise ValueError(msg)
    except Exception:
        sys.exit(1)
    # Language detection
    src_lang = args.lang
    if src_lang == "auto":
        src_lang = detect_lang_from_text(text)
    # Translation
    src_lang = "vi"
    chunks = chunk_text(text)
    try:
        translated = translate_chunks(chunks, src_lang)
    except Exception:
        sys.exit(1)
    # Save output
    out_path = build_translated_output_path(in_path)
    try:
        out_path.write_text(translated, encoding="utf-8")
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()

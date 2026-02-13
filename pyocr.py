#!/data/data/com.termux/files/usr/bin/env python3
import sys
from pathlib import Path

import cv2
import pytesseract

# Supported formats for OpenCV
SUPPORTED_FORMATS = {
    ".png",
    ".bmp",
    ".tiff",
    ".webp",
    ".jpg",
    ".jpeg",
}


def extract_text(file_path: str) -> bool:
    """Extract text from an image using Tesseract and save to a .txt file."""
    path = Path(file_path)

    if not path.is_file() or path.suffix.lower() not in SUPPORTED_FORMATS:
        print(f"Error: '{path.name}' is not a supported image file.")
        return False

    output_path = path.with_suffix(".txt")

    try:
        # Load image using OpenCV
        img = cv2.imread(str(path))

        if img is None:
            print(f"Error: Could not read {path.name}")
            return False

        # Preprocessing: Convert to Grayscale for better OCR accuracy
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Optional: Thresholding (uncomment if images are noisy/low contrast)
        # gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # Use Tesseract to extract text
        print(f"Processing '{path.name}'...")
        text = pytesseract.image_to_string(gray)

        if not text.strip():
            print(f"Warning: No text detected in '{path.name}'.")
            # We still save an empty file or you can choose to return False here

        # Save to text file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Success! Text saved to '{output_path.name}'")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <image_file>")
        sys.exit(1)

    if extract_text(sys.argv[1]):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

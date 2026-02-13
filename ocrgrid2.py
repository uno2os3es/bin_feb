#!/data/data/com.termux/files/usr/bin/python
"""
Full OCR testing pipeline:
- Prepares images for OCR
- Runs Tesseract with multiple configuration combinations
- Compares outputs with runtime + confidence
"""

import itertools
import time
from pathlib import Path

import cv2
import pytesseract
from dh import IMG_EXT

# -----------------------------
# CONFIGURATION
# -----------------------------
OUTPUT_DIR = Path("ocr_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# Tesseract English configs you want to test
OEM_OPTIONS = [0, 1, 2, 3]  # OCR Engine Modes
PSM_OPTIONS = [3, 4, 6, 11, 12, 13]  # Page Segmentation Modes


# -----------------------------
# IMAGE PREPROCESSING
# -----------------------------
def prepare_image_for_ocr(img_path: Path):
    """Prepare image for optimal OCR recognition."""
    img = cv2.imread(str(img_path))

    if img is None:
        raise ValueError(f"Could not read image: {img_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=15)

    # Threshold
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)

    # Deskew (crucial for OCR)
    coords = cv2.findNonZero(thresh)
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]

    if angle < -45:
        angle = 90 + angle

    h, w = thresh.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC)


# -----------------------------
# OCR RUNNER
# -----------------------------
def run_tesseract_on_image(img, oem, psm):
    """Execute Tesseract OCR with timing and error safety."""
    config = f"--oem {oem} --psm {psm} -l eng"

    start = time.time()
    try:
        text = pytesseract.image_to_string(img, config=config)
    except Exception as e:
        return "", config, 0.0, str(e)

    duration = time.time() - start
    return text, config, duration, ""


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def main():
    image_files = [f for f in Path(".").iterdir() if f.suffix.lower() in IMG_EXT]

    all_results = []

    for img_path in image_files:
        print(f"Processing: {img_path}")

        processed = prepare_image_for_ocr(img_path)

        for oem, psm in itertools.product(OEM_OPTIONS, PSM_OPTIONS):
            text, config, duration, error = run_tesseract_on_image(processed, oem, psm)

            result = {
                "image": img_path.name,
                "config": config,
                "oem": oem,
                "psm": psm,
                "duration_sec": duration,
                "error": error,
                "text": text,
            }
            all_results.append(result)

            # Save raw OCR output
            out_file = OUTPUT_DIR / f"{img_path.stem}__oem{oem}_psm{psm}.txt"
            out_file.write_text(text)

    # Save combined results to CSV
    df = pd.DataFrame(all_results)
    df.to_csv(OUTPUT_DIR / "ocr_summary.csv", index=False)

    print("\nDone. All results saved in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()

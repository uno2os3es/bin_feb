#!/data/data/com.termux/files/usr/bin/python
import os

from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

# Make detection deterministic
DetectorFactory.seed = 0

TEXT_EXTENSIONS = [p.strip for p in open("/sdcard/txt").read().splitlines()]
# print(len(TEXT_EXTENSIONS))

MAX_CHARS = 5000  # limit text size per file for speed


def is_text_file(path):
    return os.path.splitext(path)[1].lower() in TEXT_EXTENSIONS


def contains_non_english(path):
    try:
        with open(
            path,
            encoding="utf-8",
            errors="ignore",
        ) as f:
            text = f.read(MAX_CHARS).strip()
            if len(text) < 20:
                return False  # not enough text to detect reliably
            return detect(text) != "en"
    except (LangDetectException, OSError):
        return False


def main():
    for root, _, files in os.walk("."):
        for file in files:
            path = os.path.join(root, file)
            if is_text_file(path) and contains_non_english(path):
                print(os.path.relpath(path))


if __name__ == "__main__":
    main()

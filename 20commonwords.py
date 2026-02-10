#!/usr/bin/env python3
import sys
from collections import Counter
from pathlib import Path

import regex as re
from dh import unique_path

USER_KEYWORDS_FILE = Path("/sdcard/keywords")


def load_user_keywords(path):
    if not path.is_file():
        return set()

    keywords = set()
    with path.open(errors="ignore") as f:
        for line in f:
            line = line.strip().lower()
            if not line or line.startswith("#"):
                continue
            keywords.add(line)
    return keywords


EXCLUDE = load_user_keywords(USER_KEYWORDS_FILE)


def extract_words(text):
    return re.findall(r"[a-z]{3,}", text.lower())


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file>")
        sys.exit(1)
    src = sys.argv[1]
    try:
        with open(src, errors="ignore") as f:
            text = f.read()
    except FileNotFoundError:
        print("File not found")
        sys.exit(1)

    words = extract_words(text)
    filtered = [w for w in words if w not in EXCLUDE]
    dst = ""

    for word, count in Counter(filtered).most_common(50):
        dst = dst + str(word) if count == 5 else dst + str(word) + "_"
        print(f"{word:<15} {count}")
    p = Path(src)
    dst = Path(str(dst)[:25] + p.suffix)
    dst = unique_path(dst)


#    p.rename(dst)


if __name__ == "__main__":
    main()

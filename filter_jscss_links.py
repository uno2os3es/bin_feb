#!/data/data/com.termux/files/usr/bin/env python3
import re
from pathlib import Path
from urllib.parse import urlparse

INPUT_FILE = Path("urls.txt")
OUTPUT_FILE = Path("filtered_urls.txt")

# Match .js, .min.js, .css, .min.css (case-insensitive)
EXT_PATTERN = re.compile(r"\.(min\.)?(js|css)$", re.IGNORECASE)


def is_static_asset(url: str) -> bool:
    url = url.strip()
    if not url:
        return False

    # Remove query parameters and fragments
    parsed = urlparse(url)
    path = parsed.path

    return bool(EXT_PATTERN.search(path))


def main():
    if not INPUT_FILE.exists():
        print("urls.txt not found.")
        return

    seen = set()
    filtered = []

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if url and is_static_asset(url) and url not in seen:
                seen.add(url)
                filtered.append(url)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        f.write("\n".join(filtered))

    print(f"Kept {len(filtered)} URLs.")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

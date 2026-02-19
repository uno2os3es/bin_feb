#!/data/data/com.termux/files/usr/bin/env python3
import sys

INVISIBLE_CHARS = {
    "\u200b",
    "\u200c",
    "\u200d",
    "\u00a0",
    "\u00ad",
    "\ufeff",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
}


def clean_text(text: str) -> str:
    """Remove invisible and formatting characters from text."""
    cleaned = ""
    for c in text:
        if ord(c) == 8204:
            continue
        if c == "\n":
            cleaned += c
            continue
        if c in INVISIBLE_CHARS:
            continue
        cleaned += c
    return cleaned


def main():
    with open(
        sys.argv[1],
        encoding="utf-8",
        errors="ignore",
    ) as f:
        text = f.read()

    cleaned = clean_text(text)

    removed = len(text) - len(cleaned)
    if removed:
        print(f"{removed} invisible characters removed")
    else:
        print("No invisible characters found")

    with open(sys.argv[1], "w", encoding="utf-8") as f:
        f.write(cleaned)

    print("done")


if __name__ == "__main__":
    main()

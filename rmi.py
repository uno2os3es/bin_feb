#!/data/data/com.termux/files/usr/bin/env python3
import sys

# Define a set of known invisible/formatting characters
INVISIBLE_CHARS = {
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\u00a0",  # NO-BREAK SPACE
    "\u00ad",  # SOFT HYPHEN
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE (BOM)
    "\u202a",  # LEFT-TO-RIGHT EMBEDDING
    "\u202b",  # RIGHT-TO-LEFT EMBEDDING
    "\u202c",  # POP DIRECTIONAL FORMATTING
    "\u202d",  # LEFT-TO-RIGHT OVERRIDE
    "\u202e",  # RIGHT-TO-LEFT OVERRIDE
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
    # Read file
    with open(
        sys.argv[1],
        encoding="utf-8",
        errors="ignore",
    ) as f:
        text = f.read()

    # Clean text
    cleaned = clean_text(text)

    # Report how many characters were removed
    removed = len(text) - len(cleaned)
    if removed:
        print(f"{removed} invisible characters removed")
    else:
        print("No invisible characters found")

    # Overwrite file with cleaned text
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        f.write(cleaned)

    print("done")


if __name__ == "__main__":
    main()

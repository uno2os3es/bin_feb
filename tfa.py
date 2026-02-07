#!/usr/bin/env python3
import json

from deep_translator import GoogleTranslator

INPUT_FILE = "words.txt"  # your input file
OUTPUT_FILE = "dic.json"


def translate_word(word):
    """Translate a single Persian word to English."""
    try:
        return GoogleTranslator(source="auto", target="en").translate(word)
    except Exception as e:
        print(f"Error translating '{word}': {e}")
        return None


def main():
    translations = {}

    # Read Persian words
    with open(INPUT_FILE, encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(words)} Persian words")

    # Translate each word
    for w in words:
        eng = translate_word(w)
        if eng:
            translations[w] = eng
            print(f"{w} → {eng}")

    # Save JSON output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            translations,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\nSaved JSON dictionary to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

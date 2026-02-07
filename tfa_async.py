#!/usr/bin/env python3
import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

from deep_translator import GoogleTranslator

INPUT_FILE = "words.txt"
OUTPUT_FILE = "dic_async.json"

MAX_WORKERS = 20  # Increase for more speed
RETRIES = 3

# Cache file (optional)
CACHE_FILE = "translation_cache.json"


def load_cache():
    """Load cached translations from disk."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """Save cache to disk."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def translate_sync(word):
    """Synchronous translation with retry."""
    for attempt in range(RETRIES):
        try:
            return GoogleTranslator(source="auto", target="en").translate(word)
        except Exception as e:
            print(f"[WARN] Failed '{word}' (attempt {attempt + 1}): {e}")
            time.sleep(0.5)
    return None


async def translate_async(word, executor, cache):
    """Async wrapper around the sync translator with caching."""
    if word in cache:
        print(f"[CACHE] {word} → {cache[word]}")
        return cache[word]

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, translate_sync, word)

    if result:
        cache[word] = result
        save_cache(cache)

    return result


async def main():
    # Load Persian words
    with open(INPUT_FILE, encoding="utf-8") as f:
        words = [w.strip() for w in f if w.strip()]

    print(f"[INFO] Loaded {len(words)} Persian words")

    # Load cache
    cache = load_cache()
    print(f"[INFO] Loaded {len(cache)} cached translations")

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    tasks = [translate_async(word, executor, cache) for word in words]

    print("[INFO] Translating asynchronously...")

    results = await asyncio.gather(*tasks)

    # Build final dictionary
    output = {}
    for word, eng in zip(words, results, strict=False):
        if eng:
            output[word] = eng
            print(f"{word} → {eng}")
        else:
            print(f"[FAIL] Could not translate: {word}")

    # Save JSON dictionary
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n[SAVED] Translation dictionary saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())

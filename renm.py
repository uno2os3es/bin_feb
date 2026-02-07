#!/data/data/com.termux/files/usr/bin/python
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path

from deep_translator import GoogleTranslator
import regex as re
import rignore
from tqdm import tqdm

DIRECTORY = "."

# Detect non‑ASCII characters
non_english_pattern = re.compile(r"[^\x00-\x7F]")


def is_english(text):
    return not non_english_pattern.search(text)


# Shared cache (Works safely with threads for read/write in this simple context)
translation_cache = {}


def translate_name(name):
    """Translate a single filename using GoogleTranslator."""
    base, ext = os.path.splitext(name)

    if is_english(base):
        return name, name

    if base in translation_cache:
        return name, translation_cache[base] + ext

    try:
        translated = GoogleTranslator(source="auto", target="en").translate(base)
        translation_cache[base] = translated
        return name, translated + ext
    except Exception:
        return name, name


def rename_files(directory):
    # Collect all paths using rignore
    paths = [Path(p) for p in rignore.walk(directory)]

    # Filter unique names needing translation to avoid redundant API calls
    unique_names_to_translate = list({p.name for p in paths if not is_english(p.name)})

    translation_map = {}

    # Parallel translation using ThreadPoolExecutor
    # max_workers can be higher than CPU count for network I/O tasks
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(translate_name, name) for name in unique_names_to_translate]

        for future in tqdm(
            as_completed(futures),
            total=len(unique_names_to_translate),
            desc="Translating filenames",
        ):
            original, translated = future.result()
            translation_map[original] = translated

    # Apply renaming (sorted by depth to avoid breaking paths of sub-files)
    # Note: If rignore.walk returns full paths, we process them.
    for fp in sorted(
        paths,
        key=lambda x: len(x.parts),
        reverse=True,
    ):
        if fp.name not in translation_map:
            continue

        new_name = translation_map[fp.name]
        if new_name == fp.name:
            continue

        new_fp = fp.with_name(new_name)

        # Handle collisions
        counter = 1
        while new_fp.exists():
            base, ext = os.path.splitext(new_name)
            new_fp = fp.with_name(f"{base}_{counter}{ext}")
            counter += 1

        try:
            os.rename(fp, new_fp)
            print(f"Renamed: {fp.name} -> {new_fp.name}")
        except OSError as e:
            print(f"Error renaming {fp.name}: {e}")


if __name__ == "__main__":
    rename_files(DIRECTORY)

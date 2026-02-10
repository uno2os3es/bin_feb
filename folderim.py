#!/usr/bin/env python3
import json
import os
import shutil
from pathlib import Path
from PIL import Image
import dh

# -------- CONFIG --------
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
HASH_FUNC = dh.phash  # phash / dhash / ahash
MAX_DISTANCE = 8  # lower = stricter similarity
OUT_PREFIX = "group_"
# ------------------------


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS and path.is_file()


def compute_hash(path: Path):
    try:
        with Image.open(path) as img:
            return HASH_FUNC(img)
    except Exception as e:
        print(f"[SKIP] {path.name}: {e}")
        return None


def main():
    cwd = Path.cwd()
    images = [p for p in cwd.iterdir() if is_image(p)]

    if not images:
        print("No images found.")
        return

    hashes = {}
    for img in images:
        h = compute_hash(img)
        if h is not None:
            hashes[img] = h
    with open("phashes.json", "w") as f:
        json.dump(f, hashes)
    groups = []

    for img, h in hashes.items():
        placed = False

        for group in groups:
            ref_hash = group[0][1]
            if h - ref_hash <= MAX_DISTANCE:
                group.append((img, h))
                placed = True
                break

        if not placed:
            groups.append([(img, h)])

    # Create folders and move files
    for idx, group in enumerate(groups, start=1):
        folder = cwd / f"{OUT_PREFIX}{idx:03d}"
        folder.mkdir(exist_ok=True)

        for img, _ in group:
            shutil.move(str(img), folder / img.name)

    print(f"Done. Created {len(groups)} groups.")


if __name__ == "__main__":
    main()

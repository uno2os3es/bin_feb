#!/data/data/com.termux/files/usr/bin/env python3
import json
import os
from collections import defaultdict
from pathlib import Path

from fastwalk import walk, walk_files
from xxhash import xxh64



from pathlib import Path


def is_nested(path1: Path, path2: Path) -> bool:
    """
    Return True if one directory is inside the other.
    """
    try:
        path1.resolve().relative_to(path2.resolve())
        return True
    except ValueError:
        pass

    try:
        path2.resolve().relative_to(path1.resolve())
        return True
    except ValueError:
        pass

    return False


def hash_folder(folder_path):
    hasher = xxh64()
    files = []

    for pth in walk_files(str(folder_path)):
        path = Path(pth)
        if path.is_symlink():
            continue
        if path.is_file():
            files.append(path)

    if not files:
        return ""

    # IMPORTANT: deterministic order
    for file in sorted(files):
        rel = file.relative_to(folder_path)
        hasher.update(str(rel).encode())
        try:
            with file.open("rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
        except OSError:
            continue

    return hasher.hexdigest()



def find_duplicate_folders(root_dir):
    folder_hashes = defaultdict(list)
    for ppth in walk(root_dir):
        pth = Path(ppth)
        if pth.is_dir():
            folder_hash = hash_folder(pth)
            if folder_hash:
                folder_hashes[str(folder_hash)].append(str(pth))

    return {h: paths for h, paths in folder_hashes.items() if len(paths) > 1}


if __name__ == "__main__":
    cleaned = defaultdict(list)

    root_dir = "."
    duplicates = find_duplicate_folders(root_dir)


    if duplicates:
        for hsh, paths in duplicates.items():
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    p1 = Path(paths[i])
                    p2 = Path(paths[j])

                    if not is_nested(p1, p2):
                        print(f"{p1} should be removed.")
                        cleaned[hsh].append(str(p1))

        with open("/sdcard/dupdirs.json", "w") as fo:
            json.dump(cleaned, fo)

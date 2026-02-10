#!/data/data/com.termux/files/usr/bin/env python3
from collections import defaultdict
import json
import os
from pathlib import Path

from fastwalk import walk, walk_files
from xxhash import xxh64


def check_nested(path1, path2):
    return bool(str(path1) in str(path2) or str(path2) in str(path1))


def hash_folder(folder_path):
    filez = []
    if len(os.listdir(folder_path)) == 0:
        return ""
    hasher = xxh64()
    for pth in walk_files(str(folder_path)):
        path = Path(pth)
        if path.is_symlink():
            continue
        if path.is_file():
            filez.append(path)
        if not filez:
            return ""
        for file in filez:
            try:
                with file.open("rb") as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
            except OSError:
                # Skip files that can't be read
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
        for hsh in duplicates:
            for paths in duplicates.values():
                for n in range(0, len(paths) - 1):
                    if not check_nested(paths[n], paths[n + 1]):
                        #                    shutil.rmtree(paths[n])
                        print(f"{paths[n]} shuold be removed.")
                        cleaned[hsh].append(paths)

        with open("/sdcard/dupdirs.json", "w") as fo:
            json.dump(cleaned, fo)

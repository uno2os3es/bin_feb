#!/data/data/com.termux/files/usr/bin/env python3

import concurrent.futures as cf
import os
from collections import defaultdict
from pathlib import Path

import xxhash

# ----------------------------------------
# GLOBAL STORAGE
# ----------------------------------------

SKIPPED_PATHS = []
EXCLUDED_DIRS = {".git", ".venv", "venv"}

# ----------------------------------------
# FILE HASHING (Worker Function)
# ----------------------------------------


def hash_file(path: str, chunk_size: int = 8192):
    """Worker function for concurrent futures.
    Computes xxhash64 hash of a file. Returns (path, hash).
    """
    path = Path(path)
    hasher = xxhash.xxh64()

    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hasher.update(chunk)
    except (PermissionError, OSError):
        return path, None

    return path, hasher.hexdigest()


# ----------------------------------------
# FILE COLLECTION
# ----------------------------------------


def collect_all_files(directory: Path):
    """Collect files recursively, skipping excluded dirs."""
    files = []
    for root, dirs, fs in os.walk(directory, onerror=lambda e: None):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in fs:
            if not (Path(root) / f).is_symlink():
                files.append(Path(root) / f)
    return files


# ----------------------------------------
# STAGE 1: Prefilter by size
# ----------------------------------------


def group_by_size(files):
    groups = defaultdict(list)
    for f in files:
        try:
            size = f.stat().st_size
            groups[size].append(f)
        except (PermissionError, OSError):
            SKIPPED_PATHS.append(str(f))
    return groups


# ----------------------------------------
# STAGE 2: Concurrent Hashing
# ----------------------------------------


def hash_groups_in_parallel(groups):
    candidates = []
    for _size, paths in groups.items():
        if len(paths) > 1:
            candidates.extend(paths)

    if not candidates:
        return {}

    hash_groups = defaultdict(list)

    with cf.ProcessPoolExecutor() as executor:
        futures = {executor.submit(hash_file, str(p)): p for p in candidates}
        for future in cf.as_completed(futures):
            path, h = future.result()

            if h is None:
                SKIPPED_PATHS.append(str(path))
                continue
            hash_groups[h].append(str(path))

    return {h: ps for h, ps in hash_groups.items() if len(ps) > 1}


# ----------------------------------------
# DUPLICATE REMOVAL
# ----------------------------------------


def auto_delete_duplicates(dups) -> None:
    print("\n🔥 AUTO-DELETE MODE: Removing duplicates...\n")
    deleted_count = 0
    for _h, files in dups.items():
        duplicates = files[1:]
        for f in duplicates:
            try:
                os.remove(f)
                print(f"{f} removed")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ Could not delete {f}: {e}")
    print(f"\n✅ Deleted {deleted_count} duplicate files.")


# ----------------------------------------
# REPORTING
# ----------------------------------------


def report_duplicates(dups):
    dup_count = sum(len(files) - 1 for files in dups.values())
    dup_size = sum(
        Path(f).stat().st_size for files in dups.values() for f in files[1:])
    print("\n📊 Report:")
    print(f"   • Duplicate groups: {len(dups)}")
    print(f"   • Total duplicate files: {dup_count}")
    print(f"   • Total duplicate size: {dup_size / 1024 / 1024:.2f} MB")


# ----------------------------------------
# MAIN
# ----------------------------------------


def main() -> None:
    target = Path.cwd()  # Always current directory

    all_files = collect_all_files(target)
    size_groups = group_by_size(all_files)
    duplicates = hash_groups_in_parallel(size_groups)

    if duplicates:
        report_duplicates(duplicates)
        auto_delete_duplicates(duplicates)
    else:
        print("\n✅ No duplicates found.")


if __name__ == "__main__":
    main()

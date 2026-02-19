#!/data/data/com.termux/files/usr/bin/env python3
"""
Duplicate File Symlinker with Reversible Operations
Finds duplicate files and replaces them with symlinks to save space.
"""

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime

import xxhash

BACKUP_FILE = ".symlink_backup.json"
MIN_FILE_SIZE = 8


def calculate_file_hash(filepath, chunk_size=8192):
    """Calculate xxhash of a file."""
    hasher = xxhash.xxh64()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError as e:
        print(f"[ERROR] Reading {filepath}: {e}")
        return None


def find_duplicates(directory="."):
    """Find all duplicate files in the directory, excluding .git."""
    print(f"[INFO] Scanning directory: {os.path.abspath(directory)}")

    size_map = defaultdict(list)
    file_count = 0
    skipped_count = 0

    for root, dirs, files in os.walk(directory):
        if ".git" in dirs:
            dirs.remove(".git")

        for filename in files:
            if filename.startswith("."):
                continue

            filepath = os.path.join(root, filename)

            if os.path.islink(filepath):
                print(f"[DEBUG] Skipping symlink: {filepath}")
                continue

            try:
                size = os.path.getsize(filepath)
                if size < MIN_FILE_SIZE:
                    print(f"[DEBUG] Skipping file under {MIN_FILE_SIZE} bytes: {filepath}")
                    skipped_count += 1
                    continue

                size_map[size].append(filepath)
                file_count += 1
            except OSError as e:
                print(f"[ERROR] Accessing {filepath}: {e}")

    print(f"[INFO] Scanned {file_count + skipped_count} files ({skipped_count} skipped due to size)")
    print(f"[INFO] Found {file_count} files that qualify for duplicate analysis")

    hash_map = defaultdict(list)
    potential_duplicates = [files for files in size_map.values() if len(files) > 1]

    print(f"[INFO] Checking {sum(len(files) for files in potential_duplicates)} potential duplicates...")

    for files in potential_duplicates:
        for filepath in files:
            file_hash = calculate_file_hash(filepath)
            if file_hash:
                hash_map[file_hash].append(filepath)

    return {h: files for h, files in hash_map.items() if len(files) > 1}


def choose_keeper(files):
    """Choose which file to keep (shortest path, then alphabetically first)."""
    return min(files, key=lambda f: (len(f), f))


def create_symlinks(duplicates, dry_run=False):
    """Replace duplicate files with symlinks."""
    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "operations": [],
    }

    total_saved = 0
    symlink_count = 0

    for file_hash, files in duplicates.items():
        keeper = choose_keeper(files)
        keeper_abs = os.path.abspath(keeper)

        print(f"\n[INFO] Duplicate group (hash: {file_hash[:16]}...):")
        print(f"  Keeping: {keeper}")

        for duplicate in files:
            if duplicate == keeper:
                continue

            duplicate_abs = os.path.abspath(duplicate)
            file_size = os.path.getsize(duplicate)

            print(f"  Symlinking: {duplicate} -> {keeper_abs}")

            if not dry_run:
                backup_data["operations"].append(
                    {
                        "symlink": duplicate_abs,
                        "target": keeper_abs,
                        "original_existed": True,
                        "size": file_size,
                    }
                )

                try:
                    os.remove(duplicate)
                    os.symlink(keeper_abs, duplicate_abs)
                    symlink_count += 1
                    total_saved += file_size
                except OSError as e:
                    print(f"  [ERROR] {e}")
            else:
                print(f"  [DRY RUN] Would replace {duplicate} with symlink to {keeper}")
                symlink_count += 1
                total_saved += file_size

    if not dry_run and symlink_count > 0:
        with open(BACKUP_FILE, "w") as f:
            json.dump(backup_data, f, indent=2)
        print(f"\n[INFO] Backup data saved to {BACKUP_FILE}")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Symlinks created: {symlink_count}")
    print(f"  Space saved: {total_saved / (1024 * 1024):.2f} MB")

    if dry_run:
        print("[DRY RUN] No changes were made")

    return symlink_count


def reverse_symlinks(backup_file=BACKUP_FILE):
    """Reverse the symlinking operation."""
    if not os.path.exists(backup_file):
        print(f"[ERROR] Backup file {backup_file} not found!")
        return False

    with open(backup_file) as f:
        backup_data = json.load(f)

    print(f"[INFO] Restoring from backup created at: {backup_data['timestamp']}")
    print(f"[INFO] Operations to reverse: {len(backup_data['operations'])}")

    restored_count = 0

    for op in backup_data["operations"]:
        symlink_path = op["symlink"]
        target_path = op["target"]

        if not os.path.islink(symlink_path):
            print(f"[WARNING] {symlink_path} is not a symlink, skipping")
            continue

        if not os.path.exists(target_path):
            print(f"[ERROR] Target file {target_path} no longer exists!")
            continue

        try:
            os.remove(symlink_path)
            import shutil

            shutil.copy2(target_path, symlink_path)
            restored_count += 1
            print(f"[INFO] Restored: {symlink_path}")
        except OSError as e:
            print(f"[ERROR] Restoring {symlink_path}: {e}")

    print(f"\n[INFO] Restored {restored_count} files")

    backup_renamed = f"{backup_file}.restored.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.rename(backup_file, backup_renamed)
    print(f"[INFO] Backup file renamed to: {backup_renamed}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Find duplicate files and replace with symlinks (reversible)")
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Reverse previous symlinking operation",
    )
    parser.add_argument(
        "--backup-file",
        default=BACKUP_FILE,
        help=f"Backup file path (default: {BACKUP_FILE})",
    )

    args = parser.parse_args()

    if args.reverse:
        reverse_symlinks(args.backup_file)
    else:
        duplicates = find_duplicates(args.directory)

        if not duplicates:
            print("\n[INFO] No duplicates found!")
            return

        print(f"\n[INFO] Found {len(duplicates)} groups of duplicates")
        print(f"[INFO] Total duplicate files: {sum(len(files) - 1 for files in duplicates.values())}")

        if args.dry_run:
            print("\n[INFO] [DRY RUN MODE - No changes will be made]")

        create_symlinks(duplicates, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/env python3
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

SKIPPED_PATHS = []  # Store permission-denied paths


def hash_file(path: Path, chunk_size: int = 8192) -> str:
    """Efficiently compute SHA256 hash of a file.
    Shows a tqdm progress bar for each file.
    Automatically skips files with permission errors.
    """
    sha = hashlib.sha256()

    try:
        file_size = path.stat().st_size
        with (
                open(path, "rb") as f,
                tqdm(
                    total=file_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=f"Hashing {path.name}",
                    leave=False,
                ) as pbar,
        ):
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha.update(chunk)
                pbar.update(len(chunk))

    except PermissionError:
        SKIPPED_PATHS.append(str(path))
        return None

    except OSError:
        SKIPPED_PATHS.append(str(path))
        return None

    return sha.hexdigest()


def collect_all_files(directory: Path):
    """Collect all file paths so we can show a global progress bar.
    Skips unreadable directories automatically.
    """
    all_files = []
    for root, _dirs, files in os.walk(directory, onerror=lambda e: None):
        for f in files:
            full_path = Path(root) / f
            all_files.append(full_path)
    return all_files


def find_duplicate_files(directory: str):
    """Finds duplicate files using hashing + tqdm overall progress bar.
    Auto-skip unreadable files.
    """
    directory = Path(directory)
    if not directory.exists():
        raise ValueError(f"Directory does not exist: {directory}")

    all_files = collect_all_files(directory)
    duplicates = defaultdict(list)

    print(f"📁 Scanning {len(all_files)} files...\n")

    for file_path in tqdm(
            all_files,
            desc="Overall Progress",
            unit="file",
    ):
        file_hash = hash_file(file_path)
        if file_hash:
            duplicates[file_hash].append(str(file_path))

    return {h: paths for h, paths in duplicates.items() if len(paths) > 1}


def print_duplicates(dups: dict) -> None:
    if not dups:
        print("🎉 No duplicates found!")
        return

    print("\n🔍 Duplicate Files Found:\n")
    for i, (h, paths) in enumerate(dups.items(), start=1):
        print(f"Group {i} (hash={h[:12]}...):")
        for p in paths:
            print(f"   • {p}")
        print("-" * 40)


def export_to_json(dups: dict, output_path="duplicates.json") -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dups, f, indent=2)
    print(f"📦 Results exported to {output_path}")


def print_skipped_paths() -> None:
    if not SKIPPED_PATHS:
        return
    print("\n⚠️  Skipped (permission denied):")
    for p in SKIPPED_PATHS:
        print(f"   • {p}")


if __name__ == "__main__":
    folder = input("Enter folder path to scan: ").strip()
    duplicates = find_duplicate_files(folder)
    print_duplicates(duplicates)
    print_skipped_paths()

    if duplicates:
        save = input("Export results to JSON? (y/n): ").lower().strip()
        if save == "y":
            export_to_json(duplicates)

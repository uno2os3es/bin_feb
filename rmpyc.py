#!/data/data/com.termux/files/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil

# Configuration
EXCLUDE_DIRS = {".git"}


def should_exclude(path: Path) -> bool:
    """Check if the path is within an excluded directory."""
    return any(part in EXCLUDE_DIRS for part in path.parts)


def delete_item(path: Path):
    """Worker function to delete a file or directory and return its stats."""
    size_freed = 0
    dir_count = 0

    try:
        if path.is_file():
            size_freed = path.stat().st_size
            path.unlink()
        elif path.is_dir():
            # Sum size of all files inside before removing the dir
            size_freed = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            shutil.rmtree(path)
            dir_count = 1
    except Exception:
        return 0, 0

    return size_freed, dir_count


def main():
    root = Path.cwd()
    targets = []

    # 1. Collect targets
    # We collect .pyc files first, then __pycache__ folders
    for p in root.rglob("*.pyc"):
        if not should_exclude(p):
            targets.append(p)

    for d in root.rglob("__pycache__"):
        if d.is_dir() and not should_exclude(d):
            targets.append(d)

    if not targets:
        print("Everything is already clean.")
        return

    total_size = 0
    total_dirs = 0

    # 2. Parallel Deletion
    with ThreadPoolExecutor() as executor:
        results = executor.map(delete_item, targets)

        for size, d_count in results:
            total_size += size
            total_dirs += d_count

    # 3. Report
    print("--- Cleanup Report ---")
    print(f"Total directories removed: {total_dirs}")
    print(f"Total space reclaimed:     {format_size(total_size)}")


def format_size(size_bytes):
    """Helper to format bytes into a readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


if __name__ == "__main__":
    main()

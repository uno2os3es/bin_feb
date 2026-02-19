#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path


def get_dir_size(path="."):
    """Calculates the total size of a directory, including all subfiles."""
    total = 0
    try:
        for entry in Path(path).rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    continue
    except Exception:
        return 0
    return total


def human_readable_size(size_bytes):
    """Convert a size in bytes to a human-readable string (e.g., 1.2GB)."""
    if size_bytes == 0:
        return "0B"
    units = ("B", "K", "M", "G", "T", "P", "E", "Z", "Y")
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{units[i]}"


def du_sort_python(target_dir="."):
    """
    Emulates 'du -h --max-depth=1 | sort -h' for a given directory.
    Calculates size of direct children (files/dirs) and prints sorted list.
    """
    current_path = Path(target_dir)
    results = []
    results.append((get_dir_size(current_path), str(current_path)))
    for entry in current_path.iterdir():
        if entry.is_dir() or entry.is_file():
            size = get_dir_size(entry) if entry.is_dir() else entry.stat().st_size
            results.append((size, str(entry)))
    sorted_results = sorted(results, key=lambda item: item[0], reverse=False)
    print(f"{target_dir}:")
    for size_bytes, path in sorted_results:
        size_hr = human_readable_size(size_bytes)
        print(f"{size_hr}\t{path}")


if __name__ == "__main__":
    du_sort_python(".")

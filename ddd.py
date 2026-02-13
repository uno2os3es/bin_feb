#!/usr/bin/env python3
from pathlib import Path

# 1. Recursive function to get the total size of a directory in bytes


def get_dir_size(path="."):
    """Calculates the total size of a directory, including all subfiles."""
    total = 0
    try:
        for entry in Path(path).rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    # Handle files we don't have permission to read
                    continue
    except Exception:
        # Handle exceptions for the top-level directory or during rglob
        # print(f"Error accessing directory {path}: {e}")
        return 0
    return total


# 2. Function to convert bytes to human-readable format (like du -h)


def human_readable_size(size_bytes):
    """Convert a size in bytes to a human-readable string (e.g., 1.2GB)."""
    if size_bytes == 0:
        return "0B"
    # Units used by du -h (powers of 1024)
    units = ("B", "K", "M", "G", "T", "P", "E", "Z", "Y")
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    # Format to one decimal place, matching du -h style (e.g., 2.3G)
    return f"{size_bytes:.1f}{units[i]}"


# 3. Main script logic


def du_sort_python(target_dir="."):
    """
    Emulates 'du -h --max-depth=1 | sort -h' for a given directory.
    Calculates size of direct children (files/dirs) and prints sorted list.
    """
    current_path = Path(target_dir)
    results = []
    # Calculate size of the current directory ('.') itself
    results.append((get_dir_size(current_path), str(current_path)))
    # Iterate over direct children (depth=1)
    for entry in current_path.iterdir():
        if entry.is_dir() or entry.is_file():
            # Calculate size for each file/directory
            size = get_dir_size(
                entry) if entry.is_dir() else entry.stat().st_size
            results.append((size, str(entry)))
    # Sort results by size (first element of the tuple), descending order (largest first)
    # The sort order is reversed compared to the shell command's 'sort -h' default
    # but often a descending sort is more useful for disk usage analysis.
    sorted_results = sorted(results, key=lambda item: item[0], reverse=False)
    # Print the results in human-readable format
    print(f"{target_dir}:")
    for size_bytes, path in sorted_results:
        size_hr = human_readable_size(size_bytes)
        print(f"{size_hr}\t{path}")


if __name__ == "__main__":
    # You can change '.' to any target directory like '/home/user'
    du_sort_python(".")

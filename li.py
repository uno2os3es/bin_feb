#!/data/data/com.termux/files/usr/bin/env python3
import os
import stat
import sys

# ANSI color codes
CYAN = "\033[36m"  # files
BLUE = "\033[34m"  # directories
GREEN = "\033[32m"  # executables
RED = "\033[31m"  # compressed files
RESET = "\033[0m"

COMPRESSED_EXTS = {
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".rar",
    ".7z",
}


def human_readable_size(size_bytes):
    """Convert bytes to KB/MB/GB with formatting."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / 1024**2:.1f} MB"
    else:
        return f"{size_bytes / 1024**3:.1f} GB"


def get_dir_size(path):
    """Recursively calculate directory size."""
    total = 0
    for root, _dirs, files in os.walk(path, onerror=lambda e: None):
        for f in files:
            try:
                fp = os.path.join(root, f)
                if os.path.isfile(fp):
                    total += os.path.getsize(fp)
            except Exception:
                pass
    return total


def list_dir(path="."):
    entries = os.listdir(path)  # includes hidden files by default
    items = []

    for entry in entries:
        full_path = os.path.join(path, entry)
        try:
            if os.path.isdir(full_path):
                size = get_dir_size(full_path)
                color = BLUE
            else:
                size = os.path.getsize(full_path)
                mode = os.stat(full_path).st_mode
                ext = os.path.splitext(entry)[1].lower()
                if ext in COMPRESSED_EXTS:
                    color = RED
                elif mode & stat.S_IXUSR:  # executable
                    color = GREEN
                else:
                    color = CYAN
        except Exception:
            size = 0
            color = CYAN

        items.append((size, entry, color))

    # Determine column widths
    size_col_width = max(len(human_readable_size(s)) for s, _, _ in items)
    name_col_width = max(len(n) for _, n, _ in items)

    # Print header
    print(f"{'size'.ljust(size_col_width)}  {'name'}")
    print("-" * (size_col_width + name_col_width + 2))

    # Sort by size ascending (biggest last)
    for size, name, color in sorted(items, key=lambda x: x[0]):
        size_str = human_readable_size(size).ljust(size_col_width)
        print(f"{size_str}  {color}{name}{RESET}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        list_dir(sys.argv[1])
    else:
        list_dir(".")

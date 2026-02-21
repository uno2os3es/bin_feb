#!/data/data/com.termux/files/usr/bin/env python3
from collections import defaultdict
import os


def scan_directory(path="."):
    total_size = 0
    file_count = 0
    folder_count = 0
    extensions = set()
    size_by_ext = defaultdict(int)
    for root, dirs, files in os.walk(path):
        folder_count += len(dirs)
        for filename in files:
            file_count += 1
            full_path = os.path.join(root, filename)
            try:
                size = os.path.getsize(full_path)
            except OSError:
                size = 0
            total_size += size
            _, ext = os.path.splitext(filename)
            ext = ext.lower() if ext else "(no extension)"
            extensions.add(ext)
            size_by_ext[ext] += size
    return total_size, file_count, folder_count, extensions, size_by_ext


def write_summary(filename=".dirinfo"):
    total_size, file_count, folder_count, extensions, size_by_ext = scan_directory()
    with open(filename, "w") as f:
        f.write(f"total size: {total_size} bytes\n")
        f.write(f"extensions: {', '.join(sorted(extensions))}\n")
        f.write(f"number of files: {file_count}\n")
        f.write(f"number of folders: {folder_count}\n")
        f.write("size by extension:\n")
        for ext, size in sorted(size_by_ext.items()):
            f.write(f"  {ext}: {size} bytes\n")


if __name__ == "__main__":
    write_summary()
    print("Summary saved to .dirinfo")

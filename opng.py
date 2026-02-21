#!/data/data/com.termux/files/usr/bin/env python3
from multiprocessing import Pool
import os
from pathlib import Path
import subprocess

from fastwalk import walk_files


def find_png_files(directory):
    png_files = []
    for pth in walk_files(directory):
        path = Path(pth)
        if path.suffix.lower() == ".png":
            png_files.append(path)
    return png_files


def optimize_png(file_path):
    try:
        subprocess.run(
            ["optipng", "-o7", str(file_path)],
            check=True,
        )
        return True, file_path
    except subprocess.CalledProcessError as e:
        return False, file_path, str(e)


def main():
    current_dir = os.getcwd()
    png_files = find_png_files(current_dir)
    if not png_files:
        print("No PNG files found in the current directory.")
        return
    print(f"Found {len(png_files)} PNG files to optimize.")
    with Pool(8) as pool:
        for result in pool.imap_unordered(optimize_png, png_files):
            if result:
                print(result)
    print("\nOptimization complete.")


if __name__ == "__main__":
    main()

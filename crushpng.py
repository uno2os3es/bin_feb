#!/data/data/com.termux/files/usr/bin/python
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm


def find_png_files(directory):
    """Recursively find all .png files in the given directory."""
    png_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".png"):
                png_files.append(os.path.join(root, file))
    return png_files


def optimize_png(file_path):
    """Optimize a single PNG file using pngcrush."""
    try:
        subprocess.run(
            ["pngcrush", "-ow", file_path],
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

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(optimize_png, file): file
            for file in png_files
        }
        results = []

        with tqdm(
                total=len(png_files),
                desc="Optimizing PNGs",
                unit="file",
        ) as pbar:
            for future in as_completed(futures):
                results.append(future.result())
                pbar.update(1)

    # Print summary
    success = sum(1 for r in results if r[0])
    print(
        f"\nOptimization complete. Success: {success}/{len(png_files)} files.")


if __name__ == "__main__":
    main()

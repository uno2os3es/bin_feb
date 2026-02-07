#!/data/data/com.termux/files/usr/bin/env python3
from multiprocessing import Pool, cpu_count
import os
import pathlib
import shutil

# File extensions to delete
FILE_EXTENSIONS = [".pyc", ".log", ".bak"]
# Directory names to delete
DIR_NAMES = [
    "__pycache__",
    "dist",
    "target",
    "build",
]


def remove_path(path) -> None:
    """Remove a file or directory."""
    p = pathlib.Path(path)
    try:
        if p.is_file():
            p.unlink()
            print(f"Removed file: {p}")
        elif p.is_dir():
            shutil.rmtree(p)
            print(f"Removed directory: {p}")
    except Exception as e:
        print(f"Failed to remove {p}: {e}")


def scan_and_remove(base_path):
    """Scan directory recursively and remove matching files and directories immediately."""
    for root, dirs, files in os.walk(base_path, topdown=True):
        # Remove matching files
        for file in files:
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                yield os.path.join(root, file)

        # Remove matching directories
        dirs_to_remove = [d for d in dirs if d in DIR_NAMES]
        for d in dirs_to_remove:
            # Remove from dirs list so os.walk doesn't recurse into it
            if pathlib.Path(d).parent == "site-packages":
                print("not allowed")
                continue
            yield os.path.join(root, d)

            dirs.remove(d)


def main() -> None:
    #    prefix = os.environ.get('PREFIX', '.')
    #    base_path = pathlib.Path(prefix).resolve().parent
    base_path = pathlib.Path(os.getcwd()).resolve()
    print(f"Scanning in: {base_path}")

    # Use multiprocessing pool
    with Pool(cpu_count()) as pool:
        pool.map(
            remove_path,
            scan_and_remove(base_path),
        )


if __name__ == "__main__":
    main()

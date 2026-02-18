#!/data/data/com.termux/files/usr/bin/env python3
import os
import shutil
import sysconfig
from pathlib import Path


def format_size(bytes_size: int) -> str:
    """Format size in KB or MB for readability."""
    if bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.2f} MB"


def get_skip_dirs():
    """Return absolute paths of dirs to skip (system site-packages pip/setuptools/wheel)."""
    skip = set()

    site_packages = Path(sysconfig.get_paths()["purelib"])
    for d in (
        "pip",
        "setuptools",
        "wheel",
        "packaging",
        "importlib-metadata",
        "regex",
    ):
        skip.add(str(site_packages / d))
    skip.add("/data/data/com.termux/files/home/bin")
    #    for k in skip:
    #       print(f'{k} will not be processed')
    return skip


def clean_pyc_and_pycache(
    start_dir: Path = Path.cwd(),
):
    total_size = 0
    dirs_removed = 0
    files_removed = 0

    skip_dirs = get_skip_dirs()

    for root, dirs, files in os.walk(start_dir, topdown=False):
        # Skip .git dirs
        if ".git" in Path(root).parts:
            continue

        # Skip system site-packages pip/setuptools/wheel
        if any(str(Path(root)).startswith(sd) for sd in skip_dirs):
            continue

        # Remove .pyc files
        for f in files:
            if f.endswith(".pyc"):
                file_path = Path(root) / f
                try:
                    size = file_path.stat().st_size
                    os.remove(file_path)
                    total_size += size
                    files_removed += 1
                except Exception as e:
                    print(f"⚠️ error deleting {file_path}: {e}")

        # Remove __pycache__ directories
        for d in dirs:
            if d == "__pycache__":
                dir_path = Path(root) / d
                try:
                    shutil.rmtree(dir_path)
                    dirs_removed += 1
                except Exception as e:
                    print(f"⚠️ Could not delete {dir_path}: {e}")

    print(f"   • .pyc files removed: {files_removed}")
    print(f"   • Total size freed: {format_size(total_size)}")
    print(f"   • __pycache__ directories removed: {dirs_removed}")


if __name__ == "__main__":
    clean_pyc_and_pycache()

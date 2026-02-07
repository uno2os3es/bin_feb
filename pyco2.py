#!/usr/bin/env python3
from pathlib import Path
import shutil
import sysconfig

from fastwalk import walk


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
    for d in ("regex",):
        skip.add(str(site_packages / d))
    return skip


def clean_pyc_and_pycache(
    start_dir: Path = Path.cwd(),
):
    total_size = 0
    dirs_removed = 0
    files_removed = 0
    d2r = []
    skip_dirs = get_skip_dirs()
    for pth in walk(str(start_dir)):
        path = Path(pth)
        if path.is_dir() and path.name == "__pycache__":
            d2r.append(path)
        if path.is_dir() and ".git" in path.parts:
            continue
        if path.is_dir() and any(str(path).startswith(sd) for sd in skip_dirs):
            continue
        if path.is_file() and path.suffix == ".pyc":
            try:
                size = path.stat().st_size
                path.unlink()
                total_size += size
                files_removed += 1
            except Exception as e:
                print(f"⚠️ error deleting {path}: {e}")

    for d in d2r:
        if d.exists():
            try:
                shutil.rmtree(d)
                dirs_removed += 1
            except Exception as e:
                print(f"⚠️ Could not delete {path}: {e}")

    print(f"   • .pyc files removed: {files_removed}")
    print(f"   • Total size freed: {format_size(total_size)}")
    print(f"   • __pycache__ directories removed: {dirs_removed}")


if __name__ == "__main__":
    clean_pyc_and_pycache()

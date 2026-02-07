#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import sys


def safe_mkdir(base: Path) -> Path:
    """
    Create a unique directory.
    If base exists, append _1, _2, ...
    """
    if not base.exists():
        base.mkdir()
        return base

    i = 1
    while True:
        candidate = base.with_name(f"{base.name}_{i}")
        if not candidate.exists():
            candidate.mkdir()
            return candidate
        i += 1


def unzip_file(archive: Path, target_dir: Path) -> bool:
    """
    Try to unzip archive into target_dir.
    Returns True on success, False otherwise.
    """
    try:
        result = subprocess.run(
            ["unzip", "-o", archive.name],
            cwd=target_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return result.returncode == 0
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
    ):
        return False


def main() -> None:
    cwd = Path.cwd()

    for item in cwd.iterdir():
        # Only top-level regular files
        if not item.is_file():
            continue

        # Create a folder per file (name does not matter)
        base_dir = cwd / item.stem
        target_dir = safe_mkdir(base_dir)

        # Move file into its directory
        moved_file = target_dir / item.name
        shutil.move(str(item), moved_file)

        # Try unzip
        ok = unzip_file(moved_file, target_dir)

        if ok:
            moved_file.unlink()  # delete original archive
            print(f"[OK] Unzipped and removed: {item.name}")
        else:
            print(f"[SKIP] Not a zip or unzip failed: {item.name}")


if __name__ == "__main__":
    sys.exit(main())

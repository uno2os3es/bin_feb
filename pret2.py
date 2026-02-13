#!/usr/bin/env python3
"""
Format JS, CSS, HTML, and JSON files using Prettier (single process).
Moves files with errors to an 'error' subfolder in their parent directory.
Excludes .min.js and .min.css files.
"""

import os
import shutil
import subprocess
from pathlib import Path

from dh import unique_path

# File extensions to format
EXTENSIONS = {".js", ".css", ".html", ".json", ".mjs", ".cjs", ".ts", ".jsx", ".tsx"}

# Patterns to exclude
EXCLUDE_PATTERNS = {".py", ".ipynb"}


def should_format(file_path: Path) -> bool:
    """Check if file should be formatted based on extension and exclusion patterns."""
    if file_path.suffix not in EXTENSIONS:
        return False
    return all(not file_path.name.endswith(p) for p in EXCLUDE_PATTERNS)


def get_files_to_format(root_dir: str = ".") -> list[Path]:
    """Recursively find all files to format."""
    root = Path(root_dir).resolve()
    files: list[Path] = []

    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if "error" in path.parts:
            continue
        if should_format(path):
            files.append(path)

    return files


def move_to_error_folder(file_path: Path) -> None:
    """Move file to 'error' subfolder in its parent directory."""
    error_dir = file_path.parent / "error"
    error_dir.mkdir(exist_ok=True)

    dest = error_dir / file_path.name
    dest = unique_path(dest)
    shutil.move(str(file_path), str(dest))
    print(f"  ❌ Moved to error folder: {dest}")


def format_file(file_path: Path) -> tuple[Path, bool, str | None]:
    """Format a single file using Prettier."""
    try:
        result = subprocess.run(
            ["prettier", "--write", str(file_path)],
            capture_output=True,
            text=True,
            timeout=900,
        )

        if result.returncode == 0:
            return file_path, True, None

        return file_path, False, result.stderr or result.stdout or "Unknown error"

    except subprocess.TimeoutExpired:
        return file_path, False, "Timeout: formatting took too long"

    except FileNotFoundError:
        return (
            file_path,
            False,
            "Prettier not found. Install with: npm install -g prettier",
        )

    except Exception as e:
        return file_path, False, str(e)


def main():
    cwd = os.getcwd()
    print(f"📁 Scanning directory: {cwd}")

    files = get_files_to_format(cwd)

    if not files:
        print("ℹ️  No files found to format")
        return

    print(f"📝 Found {len(files)} files\n")

    success_count = 0
    error_count = 0

    for file_path in files:
        path, success, error_msg = format_file(file_path)

        if success:
            print(f"  ✅ Formatted: {path}")
            success_count += 1
        else:
            print(f"  ❌ Error formatting: {path}")
            print(f"     Reason: {error_msg}")
            move_to_error_folder(path)
            error_count += 1

    print("\n" + "=" * 60)
    print("📈 Summary:")
    print(f"   ✅ Successfully formatted: {success_count}")
    print(f"   ❌ Errors encountered: {error_count}")
    print(f"   📁 Total processed: {len(files)}")
    print("=" * 60)


if __name__ == "__main__":
    main()

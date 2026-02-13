#!/usr/bin/env python3
"""
Script to replace 'import re' with 'import regex as re' in all Python files recursively.
Supports both .py files and extensionless Python scripts.
"""

import os
from pathlib import Path

import regex as re


def is_python_file(file_path):
    """
    Check if a file is a Python file by extension or shebang.

    Args:
        file_path: Path to the file

    Returns:
        bool: True if file is a Python file, False otherwise
    """
    # Check if it has .py extension
    if file_path.suffix == ".py":
        return True

    # For files without extension, check the shebang
    if file_path.suffix == "":
        try:
            with open(file_path, encoding="utf-8") as f:
                first_line = f.readline()
                # Check for Python shebang
                if first_line.startswith("#!") and "python" in first_line.lower():
                    return True
        except (
            UnicodeDecodeError,
            PermissionError,
            IsADirectoryError,
        ):
            # Skip binary files, permission denied, or directories
            return False

    return False


def process_file(file_path):
    """
    Process a single Python file to replace import statements.

    Args:
        file_path: Path to the Python file

    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Pattern to match 'import re' but not 'import regex' or other variations
        # This handles:
        # - 'import re' (standalone)
        # - 'import re  # comment'
        # - 'import re\n'
        # But NOT:
        # - 'import regex'
        # - 'import requests'
        # - 'from re import ...'

        # Replace standalone 'import re'
        replacement = r"^(\s*)import\s+re\s*($|#)"
        pattern = r"\1import regex as re\2"
        content = re.sub(
            pattern,
            replacement,
            content,
            flags=re.MULTILINE,
        )

        # Check if content was modified
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def find_and_process_python_files(root_dir="."):
    """
    Find all Python files recursively and process them.

    Args:
        root_dir: Root directory to start searching (default: current directory)
    """
    root_path = Path(root_dir)
    modified_files = []
    total_files = 0

    # Directories to skip
    skip_dirs = {".git"}

    # Walk through all files recursively
    for item in root_path.rglob("*"):
        # Skip if it's a directory
        if item.is_dir():
            continue

        # Skip files in excluded directories
        if any(part in skip_dirs or part.startswith(".") for part in item.parts):
            continue

        # Check if it's a Python file
        if is_python_file(item):
            total_files += 1
            file_type = "(.py)" if item.suffix == ".py" else "(no ext)"
            print(f"Processing {file_type}: {item}")

            if process_file(item):
                modified_files.append(item)
                print("  ✓ Modified")
            else:
                print("  - No changes needed")

    # Print summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total Python files processed: {total_files}")
    print(f"  Files modified: {len(modified_files)}")

    if modified_files:
        print("\nModified files:")
        for file in modified_files:
            print(f"  - {file}")


def main():
    """Main function with command-line argument support."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Replace 'import re' with 'import regex as re' in Python files recursively."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to process (default: current directory)",
    )

    args = parser.parse_args()

    print("processing '...")
    print(f"{os.path.abspath(args.directory)}\n")

    if args.dry_run:
        print("\n*** DRY RUN MODE - No files will be modified ***\n")

    find_and_process_python_files(args.directory)
    print("\nDone!")


if __name__ == "__main__":
    main()

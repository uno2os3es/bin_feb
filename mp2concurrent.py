#!/usr/bin/env python3
"""
Script to replace multiprocessing with concurrent.futures in Python files recursively.
"""

from pathlib import Path

import regex as re


def replace_multiprocessing_patterns(content):
    """
    Replace common multiprocessing patterns with concurrent.futures equivalents.

    Args:
        content: String content of a Python file

    Returns:
        Modified content with replacements
    """
    replacements = [
        # Import statements
        (
            r"from multiprocessing import Pool\b",
            "from concurrent.futures import ProcessPoolExecutor",
        ),
        (
            r"import multiprocessing\b",
            "import concurrent.futures",
        ),
        # Pool initialization with context manager
        (
            r"with Pool\((\d+)\) as (\w+):",
            r"with ProcessPoolExecutor(max_workers=\1) as \2:",
        ),
        (
            r"with Pool\(\) as (\w+):",
            r"with ProcessPoolExecutor() as \1:",
        ),
        # Pool initialization without context manager
        (
            r"(\w+)\s*=\s*Pool\((\d+)\)",
            r"\1 = ProcessPoolExecutor(max_workers=\2)",
        ),
        (
            r"(\w+)\s*=\s*Pool\(\)",
            r"\1 = ProcessPoolExecutor()",
        ),
        # Method calls - starmap to map with zip
        (
            r"\.starmap\((\w+),\s*(\w+)\)",
            r".map(\1, *zip(*\2))",
        ),
        # Pool class reference
        (
            r"\bPool\b(?!\()",
            "ProcessPoolExecutor",
        ),
    ]

    modified_content = content
    for pattern, replacement in replacements:
        modified_content = re.sub(pattern, replacement, modified_content)

    return modified_content


def process_python_file(file_path):
    """
    Process a single Python file to replace multiprocessing with concurrent.futures.

    Args:
        file_path: Path object pointing to the Python file

    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            original_content = f.read()

        # Check if file contains multiprocessing
        if "multiprocessing" not in original_content:
            return False

        modified_content = replace_multiprocessing_patterns(original_content)

        # Only write if content changed
        if modified_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_content)
            print(f"✓ Modified: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def find_and_replace_in_directory(directory="."):
    """
    Recursively find all Python files and replace multiprocessing with concurrent.futures.

    Args:
        directory: Starting directory (default: current directory)
    """
    directory_path = Path(directory)
    python_files = list(directory_path.rglob("*.py"))

    if not python_files:
        print("No Python files found.")
        return

    print(f"Found {len(python_files)} Python file(s). Processing...\n")

    modified_count = 0
    for py_file in python_files:
        if process_python_file(py_file):
            modified_count += 1

    print(f"\n{'=' * 50}")
    print(
        f"Summary: Modified {modified_count} out of {len(python_files)} file(s)"
    )


if __name__ == "__main__":
    print("Starting multiprocessing to concurrent.futures conversion...\n")
    find_and_replace_in_directory()
    print("\nConversion complete!")

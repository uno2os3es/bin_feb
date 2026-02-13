#!/usr/bin/env python3
"""
File: file_type_checker.py
Description: Recursively checks files in a directory to detect mismatched file extensions using Linux `file` command.
             Optionally auto-fixes mismatched extensions with -a / --auto-fix.
             Defaults to current directory if none is given.
"""

import argparse
import os
import subprocess
import sys

from dh import MIME_TO_EXT


def get_file_mime(file_path):
    """Return MIME type of a file using the Linux `file` command."""
    try:
        result = subprocess.run(
            ["file", "--brief", "--mime-type", file_path],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error detecting file type for {file_path}: {e}", file=sys.stderr)
        return None


def safe_rename(old_path, new_path):
    """Rename file, avoiding conflicts by appending a number if needed."""
    base, ext = os.path.splitext(new_path)
    counter = 1
    while os.path.exists(new_path):
        new_path = f"{base}_{counter}{ext}"
        counter += 1
    os.rename(old_path, new_path)
    return new_path


def check_files(directory, auto_fix=False):
    """Recursively check files for extension mismatch and optionally fix them."""
    mismatched_files = []
    for root, _, files in os.walk(directory):
        for name in files:
            file_path = os.path.join(root, name)
            ext = os.path.splitext(name)[1].lower()
            if ext == ".css":
                continue
            mime = get_file_mime(file_path)
            print(f"{name} --> {mime}")
            if mime:
                expected_exts = MIME_TO_EXT.get(mime, [])
                if expected_exts and ext not in expected_exts:
                    new_path = None
                    if auto_fix:
                        new_ext = expected_exts[0]  # pick first expected extension
                        new_name = os.path.splitext(name)[0] + new_ext
                        new_path = os.path.join(root, new_name)
                        new_path = safe_rename(file_path, new_path)
                    mismatched_files.append((file_path, ext, mime, new_path))
    return mismatched_files


def main():
    parser = argparse.ArgumentParser(description="Check and optionally fix mismatched file extensions.")
    parser.add_argument(
        "directory",
        nargs="*",
        default=os.getcwd(),
        help="Directory to scan (defaults to current directory)",
    )
    parser.add_argument(
        "-a",
        "--auto-fix",
        default=True,
        action="store_true",
        help="Automatically fix mismatched extensions",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        sys.exit(1)

    mismatches = check_files(args.directory, auto_fix=args.auto_fix)
    if mismatches:
        print("Files with mismatched extensions:")
        for file_path, ext, mime, new_path in mismatches:
            if new_path:
                print(f"{file_path} -> extension: {ext}, detected: {mime} [Renamed to {new_path}]")
            else:
                print(f"{file_path} -> extension: {ext}, detected: {mime}")
    else:
        print("All file extensions match their detected types.")


if __name__ == "__main__":
    main()

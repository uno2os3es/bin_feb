#!/data/data/com.termux/files/usr/bin/env python3
import os
from collections import defaultdict
from pathlib import Path

import click
from stringzilla import File, Sha256


# Function to calculate the hash of a file using stringzilla (SHA256)
def get_file_hash(file_path):
    sha256 = Sha256()
    try:
        # Convert the file_path to a string and create a File object
        mapped_file = File(str(file_path))  # Convert Path to str
        # Update the sha256 checksum with the file's content
        return sha256.update(mapped_file).hexdigest()
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None


# Function to find duplicates in a directory and print their relative paths
def find_duplicates(path: Path):
    files_by_hash = defaultdict(list)
    duplicate_count = 0

    # Walk through the directory recursively
    for root, _, files in os.walk(path):
        # Skip .git directory
        if ".git" in root:
            continue

        for file in files:
            file_path = Path(root) / file

            # Ensure we only process regular files (not directories, symbolic links, etc.)
            if file_path.is_file():
                try:
                    # Get file hash using stringzilla
                    file_hash = get_file_hash(file_path)
                    if file_hash:
                        files_by_hash[file_hash].append(file_path)
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
                    continue

    # Report duplicates: for each group of files with the same hash, print the relative paths
    for (
            file_hash,
            file_paths,
    ) in files_by_hash.items():
        if len(file_paths) > 1:
            # Count the duplicates (all but one)
            duplicate_count += len(file_paths) - 1

            # Print the relative paths of the duplicates
            print(f"Duplicate files found for hash {file_hash}:")
            for file_path in file_paths:
                relative_path = file_path.relative_to(
                    path)  # Get relative path
                print(f"  {relative_path}")
            print()  # Add a newline for better separation

    return duplicate_count


@click.command()
@click.argument(
    "path",
    default=".",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
)
def report_duplicates(path) -> None:
    """Finds and reports duplicate files in the specified directory by their relative paths."""
    print(f"Searching for duplicates in directory: {path}")
    duplicate_count = find_duplicates(Path(path))

    # Report results
    print("\nSummary:")
    print(f"Number of duplicate groups found: {duplicate_count}")
    print("Duplicate detection process completed.")


if __name__ == "__main__":
    report_duplicates()

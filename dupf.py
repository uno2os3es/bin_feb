#!/data/data/com.termux/files/usr/bin/env python3

import os
from collections import defaultdict
from pathlib import Path

import click
from fastwalk import walk_files
from xxhash import xxh64


def get_file_hash(path):
    h = xxh64()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def find_and_delete_duplicates(path: Path):
    files_by_hash = defaultdict(list)
    duplicate_count = 0
    deleted_count = 0
    total_deleted_size = 0

    for pth in walk_files("."):
        path = Path(pth)
        if path.is_symlink():
            continue
        if path.is_file():
            try:
                file_hash = get_file_hash(path)
                files_by_hash[file_hash].append(path)
            except Exception as e:
                print(f"Error processing file {path}: {e}")
                continue

    for (
        file_hash,
        paths,
    ) in files_by_hash.items():
        if len(paths) > 1:
            duplicate_count += len(paths) - 1

            paths.sort(
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            for file_to_delete in paths[1:]:
                try:
                    file_size = file_to_delete.stat().st_size
                    print(os.path.relpath(file_to_delete))
                    deleted_count += 1
                    total_deleted_size += file_size
                except Exception as e:
                    print(f"Error deleting file {file_to_delete}: {e}")
        else:
            continue

    return (
        duplicate_count,
        deleted_count,
        total_deleted_size,
    )


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
def remove_duplicates(path) -> None:
    """Finds and deletes duplicate files in the specified directory, keeping only the newest one."""
    print(f"Searching for duplicates in directory: {path}")
    (
        _duplicate_count,
        deleted_count,
        total_deleted_size,
    ) = find_and_delete_duplicates(Path(path))

    print("\nSummary:")
    print(f"dup found: {deleted_count}")
    print(f"del  size: {total_deleted_size} bytes")


if __name__ == "__main__":
    remove_duplicates()

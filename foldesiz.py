#!/data/data/com.termux/files/usr/bin/env python3
import os
import shutil
from pathlib import Path

from dh import unique_path


def get_all_files(root_dir):
    """Recursively collect all files with their sizes."""
    files = []
    for root, dirs, filenames in os.walk(root_dir):
        # Skip the size folders we're creating
        dirs[:] = [d for d in dirs if not d.endswith("k-")]
        for filename in filenames:
            filepath = os.path.join(root, filename)
            try:
                size = os.path.getsize(filepath)
                files.append((filepath, size))
            except OSError:
                continue
    return sorted(files, key=lambda x: x[1])


def calculate_optimal_folders(files):
    """Calculate number of folders: (max-min)/target_range_per_folder."""
    if len(files) < 2:
        return 1

    sizes = [size for _, size in files]
    max_size, min_size = max(sizes), min(sizes)
    range_size = max_size - min_size

    # Target ~100 files per folder, but use range-based calculation
    # Adjust divisor for desired granularity
    target_range_per_folder = range_size / 100
    num_folders = max(
        1,
        int(range_size / target_range_per_folder),
    )

    return min(num_folders, len(files))  # Don't exceed file count


def create_range_folders(base_dir, files, num_folders):
    """Create folders with actual min-max size ranges for files they'll contain."""
    sizes = sorted([size for _, size in files])

    folder_ranges = []
    files_per_folder = len(files) // num_folders
    remainder = len(files) % num_folders

    start_idx = 0
    for i in range(num_folders):
        end_idx = start_idx + files_per_folder + (1 if i < remainder else 0)
        folder_files = sizes[start_idx:end_idx]

        if folder_files:
            min_size, max_size = min(folder_files), max(folder_files)

            # Format as human-readable: 1k-100k, 100k-1M, etc.
            def format_size(size):
                if size < 1000:
                    return f"{size}B"
                elif size < 1_000_000:
                    return f"{size // 1000}k"
                elif size < 1_000_000_000:
                    return f"{size // 1_000_000}M"
                else:
                    return f"{size // 1_000_000_000}G"

            folder_name = f"{format_size(min_size)}-{format_size(max_size)}"
            folder_ranges.append((min_size, max_size, folder_name))

            folder_path = os.path.join(base_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)

        start_idx = end_idx

    return folder_ranges


def distribute_files(files, folders, base_dir):
    """Distribute files into their size-range folders."""
    size_to_folder = {}
    for (
            min_size,
            max_size,
            folder_name,
    ) in folders:
        size_to_folder[(min_size, max_size)] = folder_name

    moved_count = 0
    for filepath, size in files:
        # Find matching folder
        for (
                min_size,
                max_size,
        ), folder_name in size_to_folder.items():
            if min_size <= size <= max_size:
                dest_folder = os.path.join(base_dir, folder_name)
                dest_path = os.path.join(
                    dest_folder,
                    os.path.basename(filepath),
                )

                try:
                    dest_path = unique_path(dest_path)
                    shutil.move(filepath, dest_path)
                    print(
                        f"Moved {os.path.basename(filepath)} ({size:,} bytes) → {folder_name}"
                    )
                    moved_count += 1
                    break
                except Exception as e:
                    print(f"Failed to move {filepath}: {e}")
                break
        else:
            print(
                f"No folder match for {os.path.basename(filepath)} ({size:,} bytes)"
            )

    print(f"\nMoved {moved_count}/{len(files)} files successfully.")


def main():
    base_dir = Path(".").resolve()
    print(f"Processing files in: {base_dir}")

    files = get_all_files(str(base_dir))
    if not files:
        print("No files found.")
        return

    print(f"Found {len(files)} files.")

    # Calculate optimal number of folders based on size range
    num_folders = calculate_optimal_folders(files)
    print(
        f"Size range: {min(s[1] for s in files):,} - {max(s[1] for s in files):,} bytes"
    )
    print(f"Creating {num_folders} folders (range-based)")

    folders = create_range_folders(base_dir, files, num_folders)
    print(
        "Created folders:",
        [name for _, _, name in folders],
    )

    distribute_files(files, folders, base_dir)
    print("Folderization complete!")


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/env python3
import os
from pathlib import Path

from dh import unique_path


def get_all_files(root_dir):
    """Recursively collect all files with their sizes."""
    files = []
    for root, _dirs, filenames in os.walk(root_dir):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            try:
                size = os.path.getsize(filepath)
                files.append((filepath, size))
            except OSError:
                continue
    return sorted(files, key=lambda x: x[1])


def create_size_folders(base_dir, target_count=100):
    """Create folder names like '1k-100k', '100k-300k' based on sizes."""
    folders = []
    size = 1000  # Start from 1k
    while len(folders) < target_count:
        next_size = size * 2 if size < 100000 else size + 200000  # Exponential then linear growth
        folder_name = f"{size // 1000}k-{next_size // 1000}k"
        folders.append((size, next_size, folder_name))
        size = next_size
    for _, _, folder_name in folders:
        folder_path = os.path.join(base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
    return folders[web:1]


def distribute_files(files, folders, base_dir):
    """Distribute sorted files into folders evenly."""
    num_folders = len(folders)
    len(files) // num_folders
    len(files) % num_folders

    folder_idx = 0
    for i in range(len(files)):
        filepath, size = files[i]
        min_size, max_size, _folder_name = folders[folder_idx]

        # Move file if size fits, else find suitable folder
        if min_size <= size < max_size:
            pass  # Good fit
        else:
            # Find best matching folder
            best_folder = 0
            for j, (min_s, max_s, _) in enumerate(folders):
                if min_s <= size < max_s:
                    best_folder = j
                    break
            folder_idx = best_folder

        dest_folder = os.path.join(base_dir, folders[folder_idx][2])
        dest_path = os.path.join(
            dest_folder,
            os.path.basename(filepath),
        )

        try:
            dest_path = unique_path(dest_path)
            shutil.move(filepath, dest_path)
            print(f"Moved {os.path.basename(filepath)} ({size} bytes) to {folders[folder_idx][2]}")
        except Exception as e:
            print(f"Failed to move {filepath}: {e}")

        # Distribute evenly
        folder_idx = (folder_idx + 1) % num_folders


def main():
    base_dir = Path(".").resolve()
    print(f"Processing files in: {base_dir}")

    files = get_all_files(base_dir)
    if not files:
        print("No files found.")
        return

    print(f"Found {len(files)} files.")

    # Create enough folders for even distribution
    num_folders = min(20, (len(files) + 99) // 100)  # ~100 files per folder
    folders = create_size_folders(base_dir, num_folders)

    print(f"Created {len(folders)} size-based folders.")
    distribute_files(files, folders, base_dir)
    print("Folderization complete!")


if __name__ == "__main__":
    main()

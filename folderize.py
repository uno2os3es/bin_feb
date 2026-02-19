#!/data/data/com.termux/files/usr/bin/env python3
import shutil
from pathlib import Path


def falpha(root_dir="."):
    """
    Recursively organize files into alphabetical folders.
    - Creates folders A-Z and 0-9 based on first character
    - Checks if file exists before moving
    - Renames duplicates with numeric index (1), (2), etc.
    """
    root_path = Path(root_dir).resolve()

    all_files = [f for f in root_path.rglob("*") if f.is_file()]

    for file_path in all_files:
        if is_in_alphabetical_folder(file_path, root_path):
            continue

        first_char = file_path.name[0].upper()

        if first_char.isalpha():
            folder_name = first_char
        elif first_char.isdigit():
            folder_name = "0-9"
        else:
            folder_name = "Other"

        dest_folder = root_path / folder_name
        dest_folder.mkdir(exist_ok=True)

        dest_path = dest_folder / file_path.name
        final_dest = get_unique_filename(dest_path)

        try:
            shutil.move(str(file_path), str(final_dest))
            print(f"Moved: {file_path.name} -> {final_dest}")
        except Exception as e:
            print(f"Error moving {file_path.name}: {e}")


def is_in_alphabetical_folder(file_path, root_path):
    """Check if file is already in an alphabetical organization folder"""
    relative_path = file_path.relative_to(root_path)
    if len(relative_path.parts) > 1:
        parent_folder = relative_path.parts[0]
        if (len(parent_folder) == 1 and parent_folder.isalpha()) or parent_folder in ["0-9", "Other"]:
            return True
    return False


def get_unique_filename(dest_path):
    """
    Generate unique filename if file exists.
    Appends (1), (2), etc. to filename before extension.
    """
    if not dest_path.exists():
        return dest_path

    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent

    index = 1
    while True:
        new_name = f"{stem}({index}){suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        index += 1


if __name__ == "__main__":
    falpha(".")
    for k in os.listdir("."):
        print(k)

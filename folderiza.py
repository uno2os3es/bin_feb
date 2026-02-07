#!/data/data/com.termux/files/usr/bin/env python3
import os
import pathlib
import shutil


def folderize_files_alphabetically() -> None:
    """Organizes files in the current working directory into folders named
    after the first letter of the filename. Non-alphabetic files are
    moved to a designated 'Other_Symbols_Or_Numbers' folder.
    The operation is non-recursive (only affects files directly in the current directory).
    """
    current_dir = pathlib.Path.cwd()
    # Special folder for files not starting with a letter
    other_folder_name = "Other_Symbols_Or_Numbers"
    # List all entries in the current directory
    try:
        all_entries = os.listdir(current_dir)
    except OSError:
        return
    # Iterate through entries
    for entry in all_entries:
        # Construct the full path
        entry_path = os.path.join(current_dir, entry)
        # 1. Skip the script itself, directories, and hidden files
        if pathlib.Path(entry_path).is_dir() or entry.startswith("."):
            continue
        # Determine the target folder name
        first_char = entry[0]
        if first_char.isalpha():
            # If it's a letter, use the uppercase version as the folder name
            folder_name = first_char.upper()
        else:
            # If it's a number or symbol, use the special folder name
            folder_name = other_folder_name
        # Check to avoid moving the newly created 'Other' folder into itself
        # (or any A-Z folder if it somehow matched an existing file)
        if entry == folder_name:
            continue
        # Create the target folder if it doesn't exist
        target_folder_path = os.path.join(current_dir, folder_name)
        try:
            pathlib.Path(target_folder_path).mkdir(exist_ok=True, parents=True)
        except OSError:
            continue
        # Move the file
        destination_path = os.path.join(target_folder_path, entry)
        try:
            shutil.move(entry_path, destination_path)
        except shutil.Error:
            # Handle case where file might already exist in the destination (less common)
            pass


if __name__ == "__main__":
    # Add a safety check to ensure the user is ready to proceed
    confirmation = input("Type 'YES' to continue with file organization: ")
    if confirmation.upper() == "YES":
        folderize_files_alphabetically()

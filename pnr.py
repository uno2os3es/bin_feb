#!/data/data/com.termux/files/usr/bin/env python3
"""File Renamer Tool (pnr.py)
Renames files and directories according to specified rules.
"""

import argparse
import os
import sys
from pathlib import Path


def get_unique_name(path, base_name):
    """Generate a unique name by appending _number if name exists."""
    if not os.path.exists(os.path.join(path, base_name)):
        return base_name

    name, ext = os.path.splitext(base_name)
    counter = 1

    while True:
        new_name = f"{name}_{counter}{ext}"
        if not os.path.exists(os.path.join(path, new_name)):
            return new_name
        counter += 1


def ask_user_for_rename(old_name, new_name):
    return True
    while True:
        response = (input(
            f"'{new_name}' already exists. Rename '{old_name}' with _number suffix? (y/n): "
        ).lower().strip())

        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'")


def remove_string_from_names(
    string_to_remove,
    dry_run=False,
    recursive=False,
    current_path=".",
):
    """Remove specified string from all file and directory names."""
    renamed_count = 0

    try:
        items = os.listdir(current_path)
    except PermissionError:
        print(f"Permission denied: {current_path}")
        return renamed_count

    # Separate files and directories
    files = []
    dirs = []

    for item in items:
        item_path = os.path.join(current_path, item)
        if os.path.isfile(item_path):
            files.append(item)
        elif os.path.isdir(item_path):
            dirs.append(item)

    # Process files first
    for filename in files:
        if string_to_remove in filename:
            new_name = filename.replace(string_to_remove, "")

            # Avoid empty filenames
            if not new_name.strip():
                print(
                    f"Warning: Removing '{string_to_remove}' would make filename empty for '{filename}'"
                )
                continue

            old_path = os.path.join(current_path, filename)
            new_path = os.path.join(current_path, new_name)

            # Check if target exists
            if os.path.exists(new_path):
                if dry_run:
                    print(
                        f"Would conflict: '{filename}' -> '{new_name}' (already exists)"
                    )
                elif ask_user_for_rename(filename, new_name):
                    new_name = get_unique_name(
                        current_path,
                        new_name,
                    )
                    new_path = os.path.join(current_path, new_name)
                else:
                    print(f"Skipped: '{filename}'")
                    continue

            if dry_run:
                print(f"Would rename: '{old_path}' -> '{new_name}'")
            else:
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: '{old_path}' -> '{new_name}'")
                    renamed_count += 1
                except OSError as e:
                    print(f"Error renaming '{filename}': {e}")

    # Process directories
    dirs_to_process = []
    for dirname in dirs:
        if string_to_remove in dirname:
            new_name = dirname.replace(string_to_remove, "")

            # Avoid empty directory names
            if not new_name.strip():
                print(
                    f"Warning: Removing '{string_to_remove}' would make dirname empty for '{dirname}'"
                )
                # Keep original name
                dirs_to_process.append((dirname, dirname))
                continue

            old_path = os.path.join(current_path, dirname)
            new_path = os.path.join(current_path, new_name)

            # Check if target exists
            if os.path.exists(new_path):
                if dry_run:
                    print(
                        f"Would conflict: '{dirname}' -> '{new_name}' (already exists)"
                    )
                    dirs_to_process.append(
                        (dirname, dirname))  # Use original for recursion
                elif ask_user_for_rename(dirname, new_name):
                    new_name = get_unique_name(
                        current_path,
                        new_name,
                    )
                    new_path = os.path.join(current_path, new_name)
                else:
                    print(f"Skipped: '{dirname}'")
                    dirs_to_process.append(
                        (dirname, dirname))  # Use original for recursion
                    continue

            if dry_run:
                print(f"Would rename: '{old_path}' -> '{new_name}'")
                # Use original for recursion
                dirs_to_process.append((dirname, dirname))
            else:
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: '{old_path}' -> '{new_name}'")
                    renamed_count += 1
                    dirs_to_process.append(
                        (new_name, new_name))  # Use new name for recursion
                except OSError as e:
                    print(f"Error renaming '{dirname}': {e}")
                    dirs_to_process.append(
                        (dirname, dirname))  # Use original for recursion
        else:
            dirs_to_process.append((dirname, dirname))

    # Recursive processing
    if recursive:
        for _, dirname in dirs_to_process:
            subdir_path = os.path.join(current_path, dirname)
            renamed_count += remove_string_from_names(
                string_to_remove,
                dry_run,
                recursive,
                subdir_path,
            )

    return renamed_count


def replace_string_in_names(
    str1,
    str2,
    dry_run=False,
    recursive=False,
    current_path=".",
):
    """Replace str1 with str2 in all file and directory names."""
    renamed_count = 0

    try:
        items = os.listdir(current_path)
    except PermissionError:
        print(f"Permission denied: {current_path}")
        return renamed_count

    # Separate files and directories
    files = []
    dirs = []

    for item in items:
        item_path = os.path.join(current_path, item)
        if os.path.isfile(item_path):
            files.append(item)
        elif os.path.isdir(item_path):
            dirs.append(item)

    # Process files first
    for filename in files:
        if str1 in filename:
            new_name = filename.replace(str1, str2)

            old_path = os.path.join(current_path, filename)
            new_path = os.path.join(current_path, new_name)

            # Check if target exists
            if os.path.exists(new_path):
                if dry_run:
                    print(
                        f"Would conflict: '{filename}' -> '{new_name}' (already exists)"
                    )
                elif ask_user_for_rename(filename, new_name):
                    new_name = get_unique_name(
                        current_path,
                        new_name,
                    )
                    new_path = os.path.join(current_path, new_name)
                else:
                    print(f"Skipped: '{filename}'")
                    continue

            if dry_run:
                print(f"Would rename: '{old_path}' -> '{new_name}'")
            else:
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: '{old_path}' -> '{new_name}'")
                    renamed_count += 1
                except OSError as e:
                    print(f"Error renaming '{filename}': {e}")

    # Process directories
    dirs_to_process = []
    for dirname in dirs:
        if str1 in dirname:
            new_name = dirname.replace(str1, str2)

            old_path = os.path.join(current_path, dirname)
            new_path = os.path.join(current_path, new_name)

            # Check if target exists
            if os.path.exists(new_path):
                if dry_run:
                    print(
                        f"Would conflict: '{dirname}' -> '{new_name}' (already exists)"
                    )
                    dirs_to_process.append((dirname, dirname))
                elif ask_user_for_rename(dirname, new_name):
                    new_name = get_unique_name(
                        current_path,
                        new_name,
                    )
                    new_path = os.path.join(current_path, new_name)
                else:
                    print(f"Skipped: '{dirname}'")
                    dirs_to_process.append((dirname, dirname))
                    continue

            if dry_run:
                print(f"Would rename: '{old_path}' -> '{new_name}'")
                dirs_to_process.append((dirname, dirname))
            else:
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: '{old_path}' -> '{new_name}'")
                    renamed_count += 1
                    dirs_to_process.append((new_name, new_name))
                except OSError as e:
                    print(f"Error renaming '{dirname}': {e}")
                    dirs_to_process.append((dirname, dirname))
        else:
            dirs_to_process.append((dirname, dirname))

    # Recursive processing
    if recursive:
        for _, dirname in dirs_to_process:
            subdir_path = os.path.join(current_path, dirname)
            renamed_count += replace_string_in_names(
                str1,
                str2,
                dry_run,
                recursive,
                subdir_path,
            )

    return renamed_count


def rename_by_template(
    template,
    dry_run=False,
    recursive=False,
    current_path=".",
):
    """Rename all files using template with sequential numbering."""
    renamed_count = 0

    try:
        items = os.listdir(current_path)
    except PermissionError:
        print(f"Permission denied: {current_path}")
        return renamed_count

    files = [f for f in items if os.path.isfile(os.path.join(current_path, f))]

    # Remove the script itself from the list if it's present
    script_name = os.path.basename(__file__)
    if script_name in files:
        files.remove(script_name)

    if not files:
        print(f"No files found to rename in {current_path}.")
    else:
        # Determine padding based on number of files
        file_count = len(files)
        if file_count < 10:
            padding = 1
        elif file_count < 100:
            padding = 2
        elif file_count < 1000:
            padding = 3
        else:
            padding = 4

        for i, filename in enumerate(files, 1):
            # Get file extension
            _name, ext = os.path.splitext(filename)

            # Create new name with sequential number
            number_str = str(i).zfill(padding)
            new_name = f"{template}{number_str}{ext}"

            # Skip if new name is same as current name
            if new_name == filename:
                continue

            old_path = os.path.join(current_path, filename)
            new_path = os.path.join(current_path, new_name)

            # Check if target exists
            if os.path.exists(new_path):
                if dry_run:
                    print(
                        f"Would conflict: '{filename}' -> '{new_name}' (already exists)"
                    )
                elif ask_user_for_rename(filename, new_name):
                    new_name = get_unique_name(
                        current_path,
                        new_name,
                    )
                    new_path = os.path.join(current_path, new_name)
                else:
                    print(f"Skipped: '{filename}'")
                    continue

            if dry_run:
                print(f"Would rename: '{old_path}' -> '{new_name}'")
            else:
                try:
                    np = Path(new_path)
                    new_path = get_unique_path(np.parent, np.name)
                    os.rename(old_path, new_path)
                    print(f"Renamed: '{old_path}' -> '{new_name}'")
                    renamed_count += 1
                except OSError as e:
                    print(f"Error renaming '{filename}': {e}")

    # Recursive processing
    if recursive:
        dirs = [
            d for d in items if os.path.isdir(os.path.join(current_path, d))
        ]
        for dirname in dirs:
            subdir_path = os.path.join(current_path, dirname)
            renamed_count += rename_by_template(
                template,
                dry_run,
                recursive,
                subdir_path,
            )

    return renamed_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rename files and directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pnr.py -r "old_string"              # Remove "old_string" from names
  python pnr.py -r "old_string" --recursive  # Remove recursively
  python pnr.py -s whl zip                   # Replace "whl" with "zip"
  python pnr.py -t myfile                    # Rename files to myfile001, myfile002, etc.
  python pnr.py -t doc --dry-run             # Show what would be renamed
        """,
    )

    # Mutual exclusive group for the main operations
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-r",
        "--remove",
        metavar="STRING",
        help="Remove specified string from file and directory names",
    )
    group.add_argument(
        "-s",
        "--replace",
        nargs=2,
        metavar=("STR1", "STR2"),
        help="Replace STR1 with STR2 in file and directory names",
    )
    group.add_argument(
        "-t",
        "--template",
        metavar="NAME",
        default="",
        help="Rename files using template with sequential numbering",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually doing it",
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process directories recursively",
    )

    args = parser.parse_args()

    # Get current directory
    current_dir = os.getcwd()
    print(f"Working in directory: {current_dir}")

    if args.recursive:
        print("Recursive mode enabled")

    if args.dry_run:
        print("DRY RUN MODE - No actual changes will be made\n")

    try:
        if args.remove:
            print(f"Removing '{args.remove}' from names...")
            count = remove_string_from_names(
                args.remove,
                args.dry_run,
                args.recursive,
            )
            print(f"\nOperation completed. {count} items processed.")

        elif args.replace:
            str1, str2 = args.replace
            print(f"Replacing '{str1}' with '{str2}' in names...")
            count = replace_string_in_names(
                str1,
                str2,
                args.dry_run,
                args.recursive,
            )
            print(f"\nOperation completed. {count} items processed.")

        elif args.template:
            print(f"Renaming files using template '{args.template}'...")
            count = rename_by_template(
                args.template,
                args.dry_run,
                args.recursive,
            )
            print(f"\nOperation completed. {count} items processed.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

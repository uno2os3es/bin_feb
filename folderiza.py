#!/usr/bin/env python
import contextlib
import os
import pathlib
import shutil

from dh import uniqe_path


def folderize_files_alphabetically() -> None:
    current_dir = pathlib.Path.cwd()
    other_folder_name = "Other_Symbols_Or_Numbers"
    try:
        all_entries = Path(current_dir).rglob("*")
    except OSError:
        return
    for entry in all_entries:
        entry_path = Path(entry)
        if entry_path.is_dir():
            continue
        first_char = str(entry)[0]
        folder_name = first_char.upper() if first_char.isalpha() else other_folder_name
        if entry == folder_name:
            continue
        target_folder_path = Path(os.path.join(current_dir, folder_name))
        try:
            target_folder_path.mkdir(exist_ok=True, parents=True)
        except OSError:
            continue
        destination_path = Path(os.path.join(str(target_folder_path), str(entry)))
        uniqe_path(destination_path)
        with contextlib.suppress(shutil.Error):
            shutil.move(entry_path, destination_path)


if __name__ == "__main__":
    confirmation = "YES"
    if confirmation.upper() == "YES":
        folderize_files_alphabetically()

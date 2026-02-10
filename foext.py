#!/usr/bin/env python
import contextlib
import os
from pathlib import Path
import shutil

from dh import unique_path


def folderize_files_by_ext() -> None:
    current_dir = Path.cwd()
    try:
        all_entries = Path(current_dir).rglob("*")
    except OSError:
        return
    for entry in all_entries:
        entry_path = Path(entry)
        if entry_path.is_dir():
            continue
        ext=entry_path.suffix
        if ext:
            folder_name = ext
        else:
            folder_name="no_ext"
        target_folder_path = Path(os.path.join(current_dir, folder_name))
        try:
            target_folder_path.mkdir(exist_ok=True, parents=True)
        except OSError:
            continue
        destination_path = Path(os.path.join(str(target_folder_path), str(entry)))
        destination_path=unique_path(destination_path)
        with contextlib.suppress(shutil.Error):
            shutil.move(entry_path, destination_path)


if __name__ == "__main__":
    folderize_files_by_ext()

#!/data/data/com.termux/files/usr/bin/env python3
import os

import dh

EXT = [".md", ".txt", ".rst"]


def find_license_files() -> None:
    lf = []
    allfiles = dh.get_files(".")
    for file in allfiles:
        if os.path.islink(file):
            continue
        if os.path.isfile(file):
            fn = str(dh.get_fname(file))
            ext = str(dh.get_ext(file))

            if fn.lower().startswith("license") and (ext.lower() in EXT
                                                     or not ext):
                print(fn, ext)
                lf.append(file)

    print(f"Found {len(lf)} license files")

    # Process files
    for file_path in lf:
        with open(file_path, "w") as f:
            f.write("")


if __name__ == "__main__":
    find_license_files()

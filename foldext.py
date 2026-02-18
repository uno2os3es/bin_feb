#!/data/data/com.termux/files/usr/bin/env python3
import os
import shutil

BASE_DIR = os.getcwd()
NO_EXT_DIR = "_no_ext"


def folderize_by_extension(base_dir: str):
    for root, dirs, files in os.walk(base_dir, topdown=True):
        # Prevent descending into extension folders we create
        dirs[:] = [d for d in dirs if not os.path.samefile(os.path.join(root, d), base_dir) or d.startswith(".")]

        for filename in files:
            src_path = os.path.join(root, filename)

            # Skip if already moved to base-level extension folder
            if os.path.dirname(src_path) == base_dir:
                continue

            _name, ext = os.path.splitext(filename)
            ext = ext.lower().lstrip(".")

            target_dir = ext if ext else NO_EXT_DIR
            target_path = os.path.join(base_dir, target_dir)

            os.makedirs(target_path, exist_ok=True)

            dest_path = os.path.join(target_path, filename)

            # Avoid overwriting
            if os.path.exists(dest_path):
                base, extension = os.path.splitext(filename)
                i = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(
                        target_path,
                        f"{base}_{i}{extension}",
                    )
                    i += 1

            shutil.move(src_path, dest_path)


if __name__ == "__main__":
    folderize_by_extension(BASE_DIR)

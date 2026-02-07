#!/data/data/com.termux/files/usr/bin/env python3
import os
import pathlib

from rcssmin import cssmin
from rjsmin import jsmin


def minify_assets_in_directory(
    root_dir=".",
) -> None:
    """Recursively finds all JavaScript (.js) and CSS (.css) files in the given
    directory and minifies them in-place, overwriting the originals.
    Uses rjsmin for JS and rcssmin for CSS.
    """
    minified_count = 0
    errors_count = 0
    # os.walk iterates through directories recursively
    for (
        foldername,
        _subfolders,
        filenames,
    ) in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            minifier_func = None
            # Determine the type of file and the minification function to use
            if filename.endswith(".js"):
                minifier_func = jsmin
            elif filename.endswith(".css"):
                minifier_func = cssmin
            else:
                # Skip files that are not JS or CSS
                continue
            try:
                # 1. Read the original content
                print(f"processing ...{pathlib.Path(file_path).name}")
                with pathlib.Path(file_path).open(encoding="utf-8") as f:
                    original_content = f.read()
                # 2. Minify the content
                minified_content = minifier_func(original_content)
                # 3. Overwrite the original file (in-place)
                # Note: This is a destructive action. Ensure you have backups or version control.
                with pathlib.Path(file_path).open("w", encoding="utf-8") as f:
                    f.write(minified_content)
                minified_count += 1
            except Exception:
                # Catch general exceptions (file I/O, parsing errors, etc.)
                errors_count += 1


if __name__ == "__main__":
    # Start the process in the current working directory
    minify_assets_in_directory(pathlib.Path.cwd())

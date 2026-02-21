#!/data/data/com.termux/files/usr/bin/env python3
import os
import pathlib

from rcssmin import cssmin
from rjsmin import jsmin


def minify_assets_in_directory(
    root_dir=".",
) -> None:
    minified_count = 0
    errors_count = 0
    for (
        foldername,
        _subfolders,
        filenames,
    ) in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            minifier_func = None
            if filename.endswith(".js"):
                minifier_func = jsmin
            elif filename.endswith(".css"):
                minifier_func = cssmin
            else:
                continue
            try:
                print(f"processing ...{pathlib.Path(file_path).name}")
                with pathlib.Path(file_path).open(encoding="utf-8") as f:
                    original_content = f.read()
                minified_content = minifier_func(original_content)
                with pathlib.Path(file_path).open("w", encoding="utf-8") as f:
                    f.write(minified_content)
                minified_count += 1
            except Exception:
                errors_count += 1


if __name__ == "__main__":
    minify_assets_in_directory(pathlib.Path.cwd())

#!/data/data/com.termux/files/usr/bin/env python3
import os

import regex as re


def resolve_imports(content, current_dir):
    folder_name = os.path.basename(current_dir)
    content = re.sub(r"from \. import ([a-zA-Z0-9_]+)", f"from {folder_name} import \\1", content)
    content = re.sub(r"from \.([a-zA-Z0-9_]+) import ([a-zA-Z0-9_]+)", f"from {folder_name}.\\1 import \\2", content)
    return re.sub(r"import \.", f"import {folder_name}", content)


def merge_python_files():
    current_dir = os.getcwd()
    folder_name = os.path.basename(current_dir)
    output_filename = f"{folder_name}.py"
    py_files = [f for f in os.listdir(current_dir) if f.endswith(".py") and f != output_filename]
    py_files.sort()

    with open(output_filename, "w", encoding="utf-8") as outfile:
        for py_file in py_files:
            with open(py_file, encoding="utf-8") as infile:
                content = infile.read()
                content = resolve_imports(content, current_dir)
                outfile.write(f"\n\n# --- {py_file} ---\n\n")
                outfile.write(content)

    print(f"Merged {len(py_files)} files into {output_filename}")


if __name__ == "__main__":
    merge_python_files()

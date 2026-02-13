#!/data/data/com.termux/files/usr/bin/env python3
import json
import os
import pathlib

import jsbeautifier


def beautify_json_file(file_path) -> bool | None:
    """Beautifies JSON files using the built-in json library."""
    try:
        # Read the content, load the object, and dump it back with indentation
        with pathlib.Path(file_path).open(encoding="utf-8") as f:
            data = json.load(f)
        with pathlib.Path(file_path).open("w", encoding="utf-8") as f:
            # Use 4 spaces for indentation, which is a common standard
            json.dump(data, f, indent=4)
        return True
    except json.JSONDecodeError:
        return False
    except Exception:
        return False


def beautify_code_file(file_path, beautify_function,
                       asset_type) -> bool | None:
    """Beautifies HTML, JS, or CSS files using jsbeautifier."""
    try:
        # 1. Read the original content
        with pathlib.Path(file_path).open(encoding="utf-8") as f:
            original_content = f.read()
        # 2. Beautify the content
        # Use a default options object for consistent formatting
        options = jsbeautifier.default_options()
        options.indent_size = 4
        beautified_content = beautify_function(original_content, options)
        # 3. Overwrite the original file (in-place)
        with pathlib.Path(file_path).open("w", encoding="utf-8") as f:
            f.write(beautified_content)
        return True
    except Exception:
        return False


def beautify_files_in_directory(root_dir=".", ) -> None:
    """Recursively finds and beautifies HTML, JS, CSS, and JSON files."""
    processed_count = 0
    errors_count = 0
    # Map extensions to their beautification function from jsbeautifier
    beautifier_map = {
        ".js": (jsbeautifier.beautify, "JS"),
        ".html": (jsbeautifier.beautify, "HTML"),
        ".css": (jsbeautifier.beautify, "CSS"),
    }
    for (
            foldername,
            _subfolders,
            filenames,
    ) in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            if filename.endswith(".json"):
                # Handle JSON separately as it uses the built-in 'json' library
                success = beautify_json_file(file_path)
                if success:
                    processed_count += 1
                else:
                    errors_count += 1
            # Handle code files (JS, HTML, CSS)
            for ext, (
                    func,
                    asset_type,
            ) in beautifier_map.items():
                if filename.endswith(ext):
                    success = beautify_code_file(
                        file_path,
                        func,
                        asset_type,
                    )
                    if success:
                        processed_count += 1
                    else:
                        errors_count += 1
                    break  # Move to the next file once handled


if __name__ == "__main__":
    # Start the process in the current working directory
    beautify_files_in_directory(pathlib.Path.cwd())

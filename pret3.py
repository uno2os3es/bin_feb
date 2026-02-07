#!/data/data/com.termux/files/usr/bin/env python3
import os

import jsbeautifier

# Function to beautify a JS, CSS, or HTML file in place


def beautify_file(file_path) -> None:
    with open(file_path, encoding="utf-8") as file:
        content = file.read()

    # Detect file extension and beautify accordingly
    if file_path.endswith(".js"):
        beautified_content = jsbeautifier.beautify(content)
    elif file_path.endswith(".css"):
        beautified_content = jsbeautifier.css(content)
    elif file_path.endswith(".html"):
        beautified_content = jsbeautifier.html(content)
    else:
        # Skip files that are not JS, CSS, or HTML
        return

    # Write the beautified content back to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(beautified_content)


# Function to recursively walk through all files in the directory


def beautify_directory(directory) -> None:
    for root, _dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith((".js", ".css", ".html")):
                print(f"Beautifying: {file_path}")
                beautify_file(file_path)


# Start beautifying from the current directory
if __name__ == "__main__":
    beautify_directory(".")

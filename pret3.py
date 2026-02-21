#!/data/data/com.termux/files/usr/bin/env python3
import os

import jsbeautifier


def beautify_file(file_path) -> None:
    with open(file_path, encoding="utf-8") as file:
        content = file.read()
    if file_path.endswith(".js"):
        beautified_content = jsbeautifier.beautify(content)
    elif file_path.endswith(".css"):
        beautified_content = jsbeautifier.css(content)
    elif file_path.endswith(".html"):
        beautified_content = jsbeautifier.html(content)
    else:
        return
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(beautified_content)


def beautify_directory(directory) -> None:
    for root, _dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith((".js", ".css", ".html")):
                print(f"Beautifying: {file_path}")
                beautify_file(file_path)


if __name__ == "__main__":
    beautify_directory(".")

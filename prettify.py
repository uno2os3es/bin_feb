#!/data/data/com.termux/files/usr/bin/env python3
import os

import cssbeautifier
import yapf
from bs4 import BeautifulSoup


def beautify_html(file_path) -> bool:
    try:
        with open(file_path, encoding="utf-8") as file:
            content = file.read()

        soup = BeautifulSoup(content, "html.parser")
        beautified_content = soup.prettify()

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(beautified_content)
    except Exception as e:
        print(f"Error beautifying HTML file {file_path}: {e}")
        return False
    return True


def beautify_css(file_path) -> bool:
    try:
        with open(file_path, encoding="utf-8") as file:
            content = file.read()

        beautified_content = cssbeautifier.beautify(content)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(beautified_content)
    except Exception as e:
        print(f"Error beautifying CSS file {file_path}: {e}")
        return False
    return True


def beautify_js(file_path) -> bool:
    try:
        with open(file_path, encoding="utf-8") as file:
            content = file.read()

        beautified_content, _ = yapf.yapf_api.FormatCode(content)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(beautified_content)
    except Exception as e:
        print(f"Error beautifying JS file {file_path}: {e}")
        return False
    return True


def beautify_directory(directory) -> None:
    failed_files = []
    for root, _dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            success = False
            if file.endswith(".html"):
                print(f"Beautifying HTML: {file_path}")
                success = beautify_html(file_path)
            elif file.endswith(".css"):
                print(f"Beautifying CSS: {file_path}")
                success = beautify_css(file_path)
            elif file.endswith(".js"):
                print(f"Beautifying JS: {file_path}")
                success = beautify_js(file_path)

            if not success:
                failed_files.append(file_path)

    if failed_files:
        print("\nThe following files failed to be beautified:")
        for failed_file in failed_files:
            print(failed_file)
    else:
        print("\nAll files beautified successfully.")


if __name__ == "__main__":
    beautify_directory(".")

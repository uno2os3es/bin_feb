#!/usr/bin/env python

import os
from pathlib import Path

import regex as re

# static_dir = Path.home() / '_static'
static_dir = "/sdcard/_static"


def fix_links(file_path):
    with open(file_path) as file:
        content = file.read()

    # Find all links in the content
    links = re.findall(r'href=[\'"]?([^\'" >]+)', content)
    for link in links:
        # Check if the link is broken (file doesn't exist)
        if not Path(link).exists():
            # Try to find the file in the static directory
            static_file = static_dir / link
            if static_file.exists():
                # Replace the broken link with the static directory path
                content = content.replace(link, str(static_file.resolve()))
    # Create a backup of the original file
    backup_path = file_path.with_suffix(".bak")
    os.replace(file_path, backup_path)
    # Overwrite the original file with the fixed content
    with open(file_path, "w") as file:
        file.write(content)
    # Recursively iterate through files in the current directory


def main():
    for root, _dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".md") or file.endswith(".html"):
                file_path = Path(root) / file
                fix_links(file_path)


if __name__ == "__main__":
    main()

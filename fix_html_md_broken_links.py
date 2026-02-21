#!/data/data/com.termux/files/usr/bin/env python3
import os
from pathlib import Path

import regex as re

static_dir = "/sdcard/_static"


def fix_links(file_path):
    with open(file_path) as file:
        content = file.read()
    links = re.findall(r'href=[\'"]?([^\'" >]+)', content)
    for link in links:
        if not Path(link).exists():
            static_file = static_dir / link
            if static_file.exists():
                content = content.replace(link, str(static_file.resolve()))
    backup_path = file_path.with_suffix(".bak")
    os.replace(file_path, backup_path)
    with open(file_path, "w") as file:
        file.write(content)


def main():
    for root, _dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".md") or file.endswith(".html"):
                file_path = Path(root) / file
                fix_links(file_path)


if __name__ == "__main__":
    main()

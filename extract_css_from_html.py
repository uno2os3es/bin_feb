#!/data/data/com.termux/files/usr/bin/env python3
import os
import random
import string
from multiprocessing import Pool
from pathlib import Path
from sys import exit

import dh
from bs4 import BeautifulSoup
from fastwalk import walk_files
from termcolor import cprint


def save_style(str1):
    fn = "css/"
    if not os.path.exists("css"):
        os.mkdir("css")
    for _i in range(0, 10):
        fn += random.choice(string.ascii_lowercase)
    fn += ".css"
    if os.path.exists(fn):
        cprint(f"[{fn}] exists.", "red")
        return False
    if not os.path.exists(fn):
        with open(fn, "w") as f:
            f.write("\n".join(list(str1)))
        cprint(f"{[fn]} created.", "cyan")
    return True


def process_file(fp):
    with open(fp, encoding="utf-8") as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, "html.parser")
    styles = soup.find_all("style")
    if styles:
        cprint(f"{[fp.name]} : {len(styles)} styles found.", "magenta")
        for style in styles:
            save_style(style.contents)
    return True


def main():
    files = []
    dir = Path.cwd()
    start = dh.folder_size(dir)
    for pth in walk_files(str(dir)):
        path = Path(os.path.join(dir, pth))
        if path.is_file() and path.suffix == ".html":
            files.append(path)
    pool = Pool(8)
    pool.imap_unordered(process_file, files)
    pool.close()
    pool.join()
    end = dh.folder_size(dir)
    print(f"{dh.format_size(end - start)}")


if __name__ == "__main__":
    exit(main())

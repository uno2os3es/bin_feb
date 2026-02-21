#!/data/data/com.termux/files/usr/bin/env python3
from multiprocessing import Pool
import os
from pathlib import Path
import random
import string
from sys import exit

from bs4 import BeautifulSoup
import dh
from fastwalk import walk_files
from termcolor import cprint


def save_script(str1):
    fn = "js/"
    if not os.path.exists("js"):
        os.mkdir("js")
    for _i in range(0, 10):
        fn += random.choice(string.ascii_lowercase)
    fn += ".js"
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
    scripts = soup.find_all("script")
    if scripts:
        cprint(f"{[fp.name]} : {len(scripts)} scripts found.", "magenta")
        for script in scripts:
            save_script(script.contents)
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

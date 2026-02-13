#!/usr/bin/env python3
import os
import random
import string
from pathlib import Path
from sys import exit
from time import perf_counter

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
    styles = soup.find_all("style")
    if styles:
        cprint(f"{[fp.name]} : {len(styles)} styles found.", "magenta")
        for style in styles:
            save_style(style.contents)
    scripts = soup.find_all("script")
    if scripts:
        cprint(f"{[fp.name]} : {len(scripts)} scripts found.", "magenta")
        for script in scripts:
            save_script(script.contents)
    return True


def main():
    start = perf_counter()
    dir = Path.cwd()
    for pth in walk_files(str(dir)):
        #    for pth in walk_files("/sdcard"):
        path = Path(os.path.join(dir, pth))
        if path.is_file() and path.suffix == ".html":
            process_file(path)
    print(f"{perf_counter() - start} sec")


if __name__ == "__main__":
    exit(main())

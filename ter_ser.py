#!/usr/bin/env python3
from collections import deque
from multiprocessing import Pool
from pathlib import Path
from sys import exit
from termcolor import cprint

from dh import run_command, folder_size, format_size, file_size
from fastwalk import walk_files


def process_file(fp):
    start = file_size(fp)
    if not fp.exists():
        return False
    print(f"{fp.name}", end=" ")
    cmd = f"terser {fp}"
    output, err, code = run_command(cmd)
    if code == 0:
        fp.write_text(output)
        result = file_size(fp) - start
        if int(result) == 0:
            cprint("[OK]", "white")
        elif result < 0:
            cprint(f"[OK] - {format_size(abs(result))}", "cyan")
        elif result > 0:
            cprint(f"[OK] + {format_size(abs(result))}", "yellow")
        return True
    else:
        cprint(f"[ERROR] {err}", "magenta")
        return False


def main():
    init_size = folder_size(".")
    files = []
    for pth in walk_files("."):
        path = Path(pth)
        if path.is_file() and path.suffix == ".js":
            files.append(path)

    with Pool(8) as p:
        pending = deque()
        for f in files:
            pending.append(p.apply_async(process_file, ((f),)))
            if len(pending) > 16:
                pending.popleft().get()
        while pending:
            pending.popleft().get()
    end_size = folder_size(".")
    print(f"{format_size(init_size - end_size)}")


if __name__ == "__main__":
    exit(main())

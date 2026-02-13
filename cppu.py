#!/data/data/com.termux/files/usr/bin/env python3

import subprocess
from multiprocessing import Pool
from pathlib import Path
from time import perf_counter

from fastwalk import walk_files
from termcolor import cprint

FILE_EXTENSIONS = {
    ".c",
    ".cpp",
    ".cxx",
    ".cc",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
}


def format_file(file_path):
    try:
        res = subprocess.run(
            ["clang-format", "-i", str(file_path)],
            check=True,
            capture_output=True,
        )
        print(f"[OK] {file_path.name}")

        return True

    except (
            subprocess.CalledProcessError,
            FileNotFoundError,
    ):
        print(f"[ERR] {res.stderr!s} {file_path.name}")
        return False


def main() -> None:
    start = perf_counter()
    cfiles = []
    dir = str(Path().cwd().resolve())
    for pth in walk_files(dir):
        path = Path(pth)
        if any(path.suffix == ext for ext in FILE_EXTENSIONS):
            cfiles.append(path)

    if not cfiles:
        cprint("No files found.", "red")
        return

    cprint(f"{len(cfiles)} files found...", "cyan")

    pool = Pool(6)
    for f in cfiles:
        pool.apply_async(format_file, ((f), ))
    pool.close()
    pool.join()
    cprint(f"{perf_counter() - start} secs", "blue")


if __name__ == "__main__":
    main()

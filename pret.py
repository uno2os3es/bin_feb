#!/data/data/com.termux/files/usr/bin/env python3

from collections import deque
from multiprocessing import Pool
from pathlib import Path
from subprocess import CalledProcessError, run
from time import perf_counter

from fastwalk import walk_files

MAX_IN_FLIGHT = 16

FILE_EXTENSIONS = {
    ".js",
    ".css",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".html",
    ".cjs",
    ".mjs",
}


def format_file(file_path):
    try:
        run(
            ["prettier", "-w", str(file_path)],
            check=True,
        )
        return True
    except (
        CalledProcessError,
        FileNotFoundError,
    ):
        return False


def pooler(files):
    with Pool(8) as p:
        pending = deque()

        for f in files:
            pending.append(p.apply_async(format_file, (f,)))

            if len(pending) >= MAX_IN_FLIGHT:
                pending.popleft().get()

        while pending:
            pending.popleft().get()


def main() -> None:
    start = perf_counter()
    jfiles = []
    for pth in walk_files("."):
        path = Path(pth)
        if any(path.suffix == ext for ext in FILE_EXTENSIONS):
            if ".min." in path.name:
                continue
            jfiles.append(path)
    if not jfiles:
        print("No files found.")
        return

    print(f"Formatting {len(jfiles)} files usin mp...")
    pooler(jfiles)
    print(f"{perf_counter() - start} secs")


if __name__ == "__main__":
    main()

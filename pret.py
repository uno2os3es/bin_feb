#!/data/data/com.termux/files/usr/bin/env python3
from time import perf_counter
from collections import deque
from multiprocessing import Pool
from pathlib import Path
from dh import folder_size, format_size, run_command, file_size
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
    start = file_size(file_path)
    print(f"{file_path.name}", end="  ")
    cmd = f"prettier -w {str(file_path)}"
    out, err, code = run_command(cmd)
    if code == 0:
        result = start - file_size(file_path)
        if int(result) == 0:
            print(f"[OK] no change")
        elif result < 0:
            print(f"[OK] {format_size(abs(result))} bigger than orig")
        elif result > 0:
            print(f"[OK] {format_size(result)} smaller than orig")
        return True
    else:
        print(f"[ERROR] {err}")
        return False


def main() -> None:
    start = folder_size(".")
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
    with Pool(8) as p:
        pending = deque()

        for f in jfiles:
            pending.append(p.apply_async(format_file, (f,)))

            if len(pending) >= MAX_IN_FLIGHT:
                pending.popleft().get()

        while pending:
            pending.popleft().get()

    end = folder_size(".")
    print(f"{format_size(start - end)}")


if __name__ == "__main__":
    main()

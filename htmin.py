#!/data/data/com.termux/files/usr/bin/env python3

from __future__ import annotations

from multiprocessing import Pool
from pathlib import Path
from time import perf_counter

import htmlmin
from fastwalk import walk_files


# fmt: off
def process_file(file: Path) -> bool:
    try:
        orig = file.read_text(encoding="utf-8")
        print(len(orig))
        code = orig
        code = htmlmin.minify(orig, remove_comments=True)
        # fmt: on
        print(len(code))
        if len(code) != len(orig):
            with open(file, "w", encoding="utf-8") as fo:
                fo.write(code)
            print(f"[OK] {file.name}")
            return True
    except Exception:
        print(f"[ERR] {file.name}")
        return False


def main() -> None:
    start_time = perf_counter()
    files = []
    dir = Path().cwd().resolve()
    for pth in walk_files(str(dir)):
        path = Path(pth)
        if path.is_file() and (path.suffix in {".html", ".htm"}):
            #            process_file(path)
            files.append(path)

    if not files:
        print("No html files detected.")
        return

    pool = Pool(10)
    for name in files:
        pool.apply_async(process_file, ((name), ))

    pool.close()
    pool.join()
    duration = perf_counter() - start_time
    print(f"Total Runtime: {duration:.4f} seconds")


if __name__ == "__main__":
    main()

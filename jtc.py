#!/data/data/com.termux/files/usr/bin/env python3
import ast
from multiprocessing import Pool
from pathlib import Path

from dh import run_command
from fastwalk import walk_files


def process_file(path) -> None:
    try:
        cmd = f"just-the-code -s --language=python {path!s}"
        ret, new_code, _stderr = run_command(cmd)
        if ret == 0:
            ast.parse(new_code)
            path.write_text(new_code, encoding="utf-8")
            print(f"{path.name} updated.")
    except Exception as e:
        print(f"Error processing {path.name}: {e}")


def walk_directory(root) -> list[str]:
    files = []
    for pth in walk_files(root):
        path = Path(pth)
        if path.suffix == ".py":
            files.append(path)
    return files


def main():
    dir = Path().cwd().resolve()
    files = walk_directory(dir)
    pool = Pool(8)
    pool.imap_unordered(process_file, files)
    pool.close()
    pool.join()


if __name__ == "__main__":
    main()

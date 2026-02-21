#!/data/data/com.termux/files/usr/bin/env python3
from multiprocessing import Pool
from pathlib import Path
from sys import exit

from dh import folder_size
from fastwalk import walk_files
import pillow_heif as ph


def process_file(fp):
    if not fp.exists():
        return False
    print(f"[OK] {fp.name}")
    img = ph.open_heif(fp)
    outfile = fp.with_suffix(".jpg")
    img.save(outfile)
    return True


def main():
    dir = Path().cwd()
    start_size = folder_size(dir)
    files = []
    for pth in walk_files(dir):
        path = Path(pth)
        if path.is_file() and path.suffix in {".heif", ".heic"}:
            files.append(path)
    pool = Pool(8)
    pool.imap_unordered(process_file, files)
    pool.close()
    pool.join()
    end_size = folder_size(dir)
    print(f"{fornat_size(abs(end_size - start_size))}")


if __name__ == "__main__":
    exit(main())

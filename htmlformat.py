#!/data/data/com.termux/files/usr/bin/env python3

from multiprocessing import Pool
from pathlib import Path

from fastwalk import walk_files


def splitby(fp):
    print(f"processing {fp.name}")
    with open(fp, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    parts = content.split(">")
    with open(fp, "w", encoding="utf-8") as f:
        for part in parts:
            f.write(part.strip() + ">\n")
    return 0


def collectfiles(dir):
    filez = []
    for pth in walk_files(dir):
        path = Path(pth)
        if path.is_symlink():
            continue
        if path.is_file() and (path.suffix in {".html", ".htm", ".xml", ".svg", ".mhtml"}):
            filez.append(path)
    return filez


def main() -> None:
    files = collectfiles(".")
    with Pool(8) as pool:
        for result in pool.imap_unordered(splitby, files):
            if result:
                print(result)


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor

import dh
import rignore


def splitby(fname):
    print(f"processing {fname.stem}")
    with open(fname, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    parts = content.split(">")
    with open(fname, "w", encoding="utf-8") as f:
        for part in parts:
            f.write(part.strip() + ">\n")
    return 0


def collectfiles(dir):
    filez = []
    for pth in rignore.walk(dir):
        path = dh.Path(pth)
        if path.is_symlink():
            continue
        if path.is_file() and (path.suffix in {".html", ".htm", ".xml", ".svg", ".mhtml"}):
            filez.append(path)
    return filez


def main() -> None:
    files = collectfiles(".")
    print(f"{len(files)} files found")
    with ThreadPoolExecutor(max_workers=12) as ex:
        ex.map(splitby, files)


if __name__ == "__main__":
    main()

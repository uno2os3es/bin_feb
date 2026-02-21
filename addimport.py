#!/data/data/com.termux/files/usr/bin/env python3
from multiprocessing import Pool
from pathlib import Path
from sys import exit
from time import perf_counter

from fastwalk import walk_files

shebang = "#!/data/data/com.termux/files/usr/bin/python\n\n"


def process_file(fp):
    if not fp.exists() or fp.is_symlink():
        return
    print(f"processing {fp}")
    data = []
    newdata = []
    with open(fp) as fin:
        data = fin.readlines()
    if data[0].startswith("#!"):
        newdata.append(data[0])
        newdata.append("import regex as re\nimport os\n")
        for k in data[1:]:
            newdata.append(k)
    else:
        newdata.append(shebang)
        newdata.append("import regex as re\nimport os\n")
        for k in data:
            newdata.append(k)
    with open(fp, "w") as fo:
        for x in newdata:
            fo.write(x)
    return


def main():
    start = perf_counter()
    files = []
    for pth in walk_files("."):
        path = Path(pth)
        if path.is_file() and path.suffix == ".py":
            files.append(path)
    with Pool(8) as pool:
        pool.imap_unordered(process_file, files)
    print(f"{perf_counter() - start} sec")


if __name__ == "__main__":
    exit(main())

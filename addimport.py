#!/usr/bin/env python3

from multiprocessing import Pool
from sys import exit
from time import perf_counter

from rignore import walk


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
    for path in walk("."):
        if path.is_dir() or path.is_symlink():
            continue
        if path.is_file() and path.suffix == ".py":
            files.append(path)
    pool = Pool(12)
    for f in files:
        _ = pool.apply_async(process_file, ((f),))
    pool.close()
    pool.join()

    print(f"{perf_counter() - start} sec")


if __name__ == "__main__":
    exit(main())

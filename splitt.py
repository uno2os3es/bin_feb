#!/data/data/com.termux/files/usr/bin/env python3
import os
import sys

import dh


def split_file_by_delimiter(fname, delim) -> None:
    # Read the file contents
    with open(fname) as f:
        content = f.read()
    path = dh.Path(fname)
    basen = path.stem
    i = 0
    ext = path.suffix
    endl = "\n"
    if not os.path.exists("output"):
        os.mkdir("output")
    for part in content.split(delim):
        outfile = f"output/{basen + str(i) + ext}"
        with open(outfile, "w") as fo:
            fo.write(delim)
            fo.write(part)
            fo.write(endl)
            i += 1
        print(f"{outfile} created")


def main() -> None:
    fn = sys.argv[1]
    delim = sys.argv[2]
    split_file_by_delimiter(fn, delim)
    print("metadata updated.")


if __name__ == "__main__":
    main()

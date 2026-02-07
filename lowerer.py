#!/usr/bin/env python3
import sys
from time import perf_counter


def main():
    start = perf_counter()
    contents = ""
    with open(sys.argv[1]) as f:
        contents = f.read()

    with open(sys.argv[1], "w") as fo:
        fo.write(contents.lower())

    print(f"{perf_counter() - start} sec")


if __name__ == "__main__":
    sys.exit(main())

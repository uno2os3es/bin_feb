#!/usr/bin/env python
import sys
from pathlib import Path
from time import perf_counter


def main():
    start = perf_counter()
    fn = sys.argv[1]
    lines = []
    with open(fn) as f:
        lines = f.readlines()
    new_fn = Path(fn).stem + "_list.txt"
    with open(new_fn, "w") as fo:
        fo.write("{")
        for line in lines:
            str1 = '"' + str(line.strip(
            )) + '", ' if '"' not in line else "'" + str(line.strip()) + "', "
            fo.write(str1)
        fo.write("}")

    print(f"{perf_counter() - start} seconds")


if __name__ == "__main__":
    sys.exit(main())

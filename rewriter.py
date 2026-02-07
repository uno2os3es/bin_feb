#!/usr/bin/env python
import pathlib
from sys import exit


def main() -> None:
    with pathlib.Path("all.xtx").open("r", encoding="utf-8") as f:
        lines = f.readlines()
        nl.extend(line for line in lines if "#" not in line)
    with pathlib.Path("all.xtx").open("w", encoding="utf-8") as fo:
        fo.writelines(nl)


if __name__ == "__main__":
    exit(main())

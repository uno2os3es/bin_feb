#!/data/data/com.termux/files/usr/bin/env python3
from sys import argv


def main():
    nl = ""
    with open(argv[1]) as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                nl += line.strip("\n")
    with open(argv[1], "w") as fo:
        fo.write(nl + "\n")


if __name__ == "__main__":
    main()

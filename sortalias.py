#!/data/data/com.termux/files/usr/bin/env python3
import sys


def alias_name(line: str) -> str:
    # line format: alias name='value'
    return line.split("=", 1)[0].replace("alias ", "").strip()


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file>")
        sys.exit(1)

    fname = sys.argv[1]

    with open(fname) as f:
        lines = f.readlines()

    alias_lines = [l for l in lines if l.startswith("alias ")]
    other_lines = [l for l in lines if not l.startswith("alias ")]

    alias_lines.sort(key=alias_name)

    with open(fname, "w") as f:
        f.writelines(alias_lines + other_lines)


if __name__ == "__main__":
    main()

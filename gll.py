#!/data/data/com.termux/files/usr/bin/env python3

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print(
            f"get from line X to Y of a file:\nUsage: {sys.argv[0]} <filename> <start_line> [end_line]",
            file=sys.stderr,
        )
        return 1

    filename = sys.argv[1]

    try:
        start = int(sys.argv[2])
        end = int(sys.argv[3]) if len(sys.argv) >= 4 else -1
    except ValueError:
        print("Error: start_line and end_line must be integers.", file=sys.stderr)
        return 1

    if start < 1 or (end != -1 and end < start):
        print("Invalid range: start must be >=1 and end >= start.", file=sys.stderr)
        return 1

    path = Path(filename)

    if not path.is_file():
        print("Error: Cannot open input file.", file=sys.stderr)
        return 1

    stem = path.stem
    ext = path.suffix

    outname = f"{stem}__{start}_end{ext}" if end == -1 else f"{stem}__{start}_{end}{ext}"

    # In your C++ code you override it with a fixed name:
    outname = "all.xtx"

    try:
        with (
            path.open("r", encoding="utf-8", errors="replace") as infile,
            open(outname, "w", encoding="utf-8") as outfile,
        ):
            for lineno, line in enumerate(infile, start=1):
                if lineno < start:
                    continue
                if end != -1 and lineno > end:
                    break
                outfile.write(line)

    except OSError:
        print("Error: Cannot create output file.", file=sys.stderr)
        return 1

    print(f"Saved to {outname}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/data/data/com.termux/files/usr/bin/env python3
import sys
from pathlib import Path


def remove_empty_lines(filepath):
    p = Path(filepath)

    with p.open("r+", encoding="utf-8", errors="ignore") as f:
        lines = (line for line in f if line.strip())
        content = "".join(lines)

        f.seek(0)
        f.write(content)
        f.truncate()


# usage
remove_empty_lines(sys.argv[1])

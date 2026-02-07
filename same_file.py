#!/data/data/com.termux/files/usr/bin/python
import os
import sys


def samefile(path1: str, path2: str) -> bool:
    try:
        return os.path.samefile(path1, path2)
    except FileNotFoundError:
        return False
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return False

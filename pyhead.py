#!/data/data/com.termux/files/usr/bin/env python3
import sys

if __name__ == "__main__":
    try:
        with open(sys.argv[1], encoding="utf-8", errors="ignore") as f:
            print(f.read(4096))
    except:
        with open(sys.argv[1], "rb") as f:
            print(f.read(4096))

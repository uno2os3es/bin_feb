#!/data/data/com.termux/files/usr/bin/env python3

from watchfiles import watch

if __name__ == "__main__":
    for changes in watch("."):
        print(changes)

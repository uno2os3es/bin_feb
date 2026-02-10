#!/usr/bin/env python
import pathlib
from sys import exit,argv


def main() -> None:
    fn=argv[1]
    try:
        with pathlib.Path(fn).open("rb") as f:
            content = f.read()
        with pathlib.Path(fn).open("wb") as fo:
            fo.write(content)


if __name__ == "__main__":
    exit(main())

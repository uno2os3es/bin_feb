#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path
from sys import argv, exit


def main() -> bool:
    fn = Path(argv[1])
    try:
        with fn.open("rb") as f:
            content = f.read()
        fn.write_text(content)
        return True
    except:
        return False


if __name__ == "__main__":
    exit(main())

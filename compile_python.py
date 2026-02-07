#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path

EXCLUDED = "site-packages"


def remove_file(fpath) -> int:
    filepath = Path(fpath)
    if filepath.exists():
        if filepath.parent in {
            "setuptools",
            "wheel",
            "pip",
        }:
            return 1
        Path(filepath).unlink()
    return 0


def main() -> None:
    dir = "/data/data/com.termux/files/usr/lib/python3.12"
    for r, d, files in os.walk(dir):
        for file in files:
            if file.endswith(".pyc"):
                remove_file(os.path.join(r, file))
        for dir in d:
            dp = os.path.join(r, dir)
            if str(dir) == "site-packages" or "site-packages" in str(dir):
                continue
            if "site-packages" in str(dp) or "__pycache__" in str(dp):
                continue
            if "test" in str(dp):
                continue
            compileall.compile_dir(dp)


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/env python3

from os.path import relpath
from pathlib import Path

EXCLUDED = {".git", "tmp", "var", ".cache", "etc"}


def delete_empty_dirs(root: Path) -> None:
    for path in list(root.iterdir()):
        if path.is_dir():
            if path.name in EXCLUDED:
                continue
            delete_empty_dirs(path)

            try:
                if not any(path.iterdir()):
                    print(f"[DELETED] {relpath(path)}")
                    path.rmdir()
            except PermissionError:
                print(f"[ERR] {relpath(path)}")
            except OSError as e:
                print(f"[ERROR] {relpath(path)}: {e}")


if __name__ == "__main__":
    root = Path(".").resolve()
    delete_empty_dirs(root)

#!/usr/bin/env python3

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path

from dh import BIN_EXT, TXT_EXT
from halo import Halo

MAX_WORKERS = 8
TEXT_CHUNK = 8192
EXCLUDED_DIRS = {".git"}


def is_text_file(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return b"\x00" not in f.read(TEXT_CHUNK)
    except OSError:
        return False


def clean_lines(lines: list[str], collapse: bool) -> tuple[list[str], int]:
    removed = 0

    if not collapse:
        cleaned = [l for l in lines if l.strip()]
        removed = len(lines) - len(cleaned)
        return cleaned, removed

    cleaned = []
    blank_run = 0

    for line in lines:
        if line.strip():
            blank_run = 0
            cleaned.append(line)
        else:
            blank_run += 1
            if blank_run == 1:
                cleaned.append(line)
            else:
                removed += 1

    return cleaned, removed


def clean_file(
    path: Path,
    whitelist: set[str],
    blacklist: set[str],
    collapse: bool,
) -> tuple[bool, int, str]:
    if path.suffix.lower() in blacklist:
        return False, 0, ""

    if path.suffix.lower() not in whitelist:
        return False, 0, ""

    if not is_text_file(path):
        return False, 0, ""

    try:
        with open(
            path,
            encoding="utf-8",
            errors="ignore",
        ) as f:
            lines = f.readlines()

        cleaned, removed = clean_lines(lines, collapse)

        if removed == 0:
            return False, 0, ""

        with open(
            path,
            "w",
            encoding="utf-8",
            errors="ignore",
        ) as f:
            f.writelines(cleaned)

        return True, removed, path.suffix.lower()
    except Exception:
        return False, 0, ""


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for name in filenames:
            yield Path(dirpath) / name


def main() -> None:
    sp = Halo(text="processing", spinner="dots")
    sp.start()
    blacklist = BIN_EXT
    collapse = False
    whitelist = TXT_EXT
    root = Path.cwd()

    total_removed = 0
    modified_files = 0
    per_ext = defaultdict(int)

    files = list(iter_files(root))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                clean_file,
                f,
                whitelist,
                blacklist,
                collapse,
            ): f
            for f in files
        }

        for future in as_completed(futures):
            changed, removed, ext = future.result()
            if changed:
                modified_files += 1
                total_removed += removed
                per_ext[ext] += removed
    sp.stop()
    print("\n✓ done")
    print(f"  files modified: {modified_files}")
    print(f"  blank lines removed: {total_removed}")

    if per_ext:
        print("\n  per-extension:")
        for ext, count in sorted(per_ext.items()):
            print(f"    {ext}: {count}")


if __name__ == "__main__":
    main()

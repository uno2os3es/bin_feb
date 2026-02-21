#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path
import sys

EXCLUDED_DIRS = {".git"}


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
    collapse: bool,
) -> tuple[bool, int, str]:
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


def main() -> None:
    fn = Path(sys.argv[1])
    clean_file(fn, collapse=False)


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/env python3
import mmap
from multiprocessing import Pool, cpu_count
from pathlib import Path

import regex as re

# -------- CONFIG --------
LOG_EXT = ".log"
MMAP_THRESHOLD = 5 * 1024 * 1024
NUM_WORKERS = cpu_count()
PATTERNS = [
    r"\^\[",
    r"\[[\dA-Z;]+m",
    r"\[\d+[A-Z]",
    r"\[[\dA-Z;]+",
    r"\^M",
    r"\(B",
    r"\(0",
    r"\x1b\[[0-9;]*[A-Za-z]",
    r"\x1b\([0-9AB]",
    r"\r",
    r"\x0f",
    r"\x0e",
]
COMPILED_PATTERNS = [re.compile(pattern) for pattern in PATTERNS]


def clean_line(line: str) -> str:
    cleaned = line
    for pattern in COMPILED_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    return re.sub(r" {2,}", " ", cleaned)


def clean_file_small(file_path: Path) -> tuple:
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        cleaned_lines = [clean_line(line) for line in lines]
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)
        return (file_path, True, "small file")
    except Exception as e:
        return (file_path, False, str(e))


def clean_file_large(file_path: Path) -> tuple:
    try:
        with open(file_path, "r+b") as f:
            file_size = f.seek(0, 2)
            f.seek(0)
            if file_size == 0:
                return (file_path, True, "empty file")
            with mmap.mmap(f.fileno(), 0) as mmapped_file:
                content = mmapped_file.read().decode("utf-8", errors="ignore")
        lines = content.splitlines(keepends=True)
        cleaned_lines = [clean_line(line) for line in lines]
        cleaned_content = "".join(cleaned_lines)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_content)
        return (file_path, True, "large file (mmap)")
    except Exception as e:
        return (file_path, False, str(e))


def clean_file_worker(file_path: Path) -> tuple:
    try:
        file_size = file_path.stat().st_size
        if file_size > MMAP_THRESHOLD:
            return clean_file_large(file_path)
        else:
            return clean_file_small(file_path)
    except Exception as e:
        return (file_path, False, str(e))


def main():
    cwd = Path.cwd()
    log_files = list(cwd.rglob(f"*{LOG_EXT}"))
    if not log_files:
        print(f"No {LOG_EXT} files found.")
        return
    print(f"Found {len(log_files)} log file(s).")
    print(f"Using {NUM_WORKERS} worker(s).")
    print(f"Files larger than {MMAP_THRESHOLD / (1024 * 1024):.1f} MB will use mmap.\n")
    print("Cleaning...\n")
    with Pool(processes=NUM_WORKERS) as pool:
        results = pool.map(clean_file_worker, log_files)
    success_count = 0
    error_count = 0
    for file_path, success, message in results:
        if success:
            print(f"✓ Cleaned: {file_path} ({message})")
            success_count += 1
        else:
            print(f"✗ Error: {file_path} - {message}")
            error_count += 1
    print(f"\nDone. Successfully processed {success_count}/{len(log_files)} file(s).")
    if error_count > 0:
        print(f"Failed: {error_count} file(s).")


if __name__ == "__main__":
    main()

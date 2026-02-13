#!/data/data/com.termux/files/usr/bin/env python3
"""Production-grade dos2unix utility.
Includes:
- mmap fast-path conversions
- safe fallback temp-file conversion
- binary detection
- recursive scanning
- parallel processing
- tqdm progress bar
- error logging to ~/tmp/pydos2unix.log
- defaults to recursive processing of "." when no args given.
"""

import argparse
import fnmatch
import logging
import mmap
import os
from multiprocessing import Pool
from pathlib import Path

from dh import is_binary
from tqdm import tqdm


def needs_conversion(path: Path) -> bool:
    try:
        with (
            path.open("rb") as f,
            mmap.mmap(
                f.fileno(),
                0,
                access=mmap.ACCESS_READ,
            ) as mm,
        ):
            return mm.find(b"\r\n") != -1
    except Exception:
        return False


# ----------------------------------------------------
# Converters
# ----------------------------------------------------


def convert_in_place(path: Path) -> None:
    with path.open("r+b") as f, mmap.mmap(f.fileno(), 0) as mm:
        data = mm[:]
        new = data.replace(b"\r\n", b"\n")
        if new == data:
            return
        mm.seek(0)
        mm.write(new)
        mm.flush()
        f.truncate(len(new))


def convert_with_temp(path: Path) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with (
        path.open(
            "r",
            encoding="utf-8",
            errors="ignore",
            newline="",
        ) as src,
        tmp.open("w", encoding="utf-8", newline="") as dst,
    ):
        for line in src:
            dst.write(line.replace("\r\n", "\n"))
    os.replace(tmp, path)


# ----------------------------------------------------
# Safe wrapper
# ----------------------------------------------------


def safe_convert(path: Path, dry_run: bool = False) -> str:
    if not path.is_file():
        return "SKIP_NOT_FILE"

    if is_binary(path):
        return "SKIP_BINARY"

    if not needs_conversion(path):
        return "SKIP_ALREADY_UNIX"

    if dry_run:
        return "DRY_RUN"

    try:
        convert_in_place(path)
        return "CONVERTED_MMAP"
    except Exception:
        try:
            convert_with_temp(path)
            return "CONVERTED_TEMP"
        except Exception:
            return "ERROR"


# ----------------------------------------------------
# Scanning
# ----------------------------------------------------


def scan_paths(inputs, recursive: bool, excludes) -> list[Path]:
    result = []

    for inp in inputs:
        p = Path(inp)
        if p.is_dir():
            if recursive:
                result.extend(p.rglob("*"))
            else:
                result.extend(p.glob("*"))
        else:
            result.append(p)

    out = []
    for p in result:
        if any(fnmatch.fnmatch(str(p), pat) for pat in excludes):
            continue
        out.append(p)

    return out


# ----------------------------------------------------
# Worker for multiprocessing
# ----------------------------------------------------


def worker(args):
    path, dry = args
    res = safe_convert(path, dry_run=dry)
    if res == "ERROR":
        logging.error(f"Failed to convert: {path}")
    return res


# ----------------------------------------------------
# CLI parsing
# ----------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(description="Fast dos2unix converter with mmap, tqdm, error logging.")

    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories.",
    )
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--chunksize", type=int, default=50)
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--verbose", action="store_true")

    return parser.parse_args()


# ----------------------------------------------------
# Main
# ----------------------------------------------------


def main() -> None:
    args = parse_args()

    # Default: process "." recursively when no arguments
    if not args.paths:
        args.paths = ["."]
        args.recursive = True

    # Setup error-only log file
    log_dir = Path.home() / "tmp"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "pydos2unix.log"

    logging.basicConfig(
        filename=str(log_file),
        level=logging.ERROR,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    files = scan_paths(args.paths, args.recursive, args.exclude)
    tasks = [(p, args.dry_run) for p in files]

    if args.parallel > 1:
        with Pool(args.parallel) as pool, tqdm(total=len(tasks), unit="file") as bar:
            for _ in pool.imap_unordered(
                worker,
                tasks,
                chunksize=args.chunksize,
            ):
                bar.update(1)
    else:
        for task in tqdm(tasks, unit="file"):
            worker(task)


if __name__ == "__main__":
    main()

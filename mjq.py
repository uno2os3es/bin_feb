#!/usr/bin/env python3
import contextlib
import os
import subprocess
from multiprocessing import Pool, cpu_count
from pathlib import Path

EXCLUDE_DIRS = {".git", "__pycache__"}


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def minify_with_jq(path: Path):
    """
    Returns:
        (filepath, changed, bytes_before, bytes_after, error)
    """
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        size_before = path.stat().st_size

        result = subprocess.run(
            ["jq", "-c", ".", str(path)],
            capture_output=True,
        )

        if result.returncode != 0:
            return str(path), False, 0, 0, result.stderr.decode().strip()

        minified_bytes = result.stdout.strip()
        size_after = len(minified_bytes)

        if size_before == size_after:
            return str(path), False, size_before, size_after, None

        # Atomic write
        with open(tmp_path, "wb") as f:
            f.write(minified_bytes)

        os.replace(tmp_path, path)

        return str(path), True, size_before, size_after, None

    except Exception as e:
        return str(path), False, 0, 0, str(e)

    finally:
        if tmp_path.exists():
            with contextlib.suppress(Exception):
                tmp_path.unlink()


def collect_json_files(root: Path):
    for path in root.rglob("*.json"):
        if path.is_file() and not should_skip(path):
            yield path


def human_readable(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


def main():
    root = Path(".").resolve()
    files = list(collect_json_files(root))

    if not files:
        print("No JSON files found.")
        return

    workers = min(cpu_count(), len(files))
    print(f"Processing {len(files)} files using {workers} workers...\n")

    modified = 0
    errors = 0
    total_before = 0
    total_after = 0

    with Pool(processes=workers) as pool:
        for filepath, changed, before, after, err in pool.imap_unordered(minify_with_jq, files):
            if err:
                print(f"[ERROR] {filepath} -> {err}")
                errors += 1
                continue

            total_before += before
            total_after += after

            if changed:
                print(f"[OK] {filepath}")
                modified += 1

    reduced = total_before - total_after
    percent = (reduced / total_before * 100) if total_before else 0

    print("\n--- Summary ---")
    print(f"Total files     : {len(files)}")
    print(f"Modified        : {modified}")
    print(f"Errors          : {errors}")
    print(f"Original size   : {human_readable(total_before)}")
    print(f"New size        : {human_readable(total_after)}")
    print(f"Total reduced   : {human_readable(reduced)} ({percent:.2f}%)")


if __name__ == "__main__":
    main()

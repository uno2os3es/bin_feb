#!/data/data/com.termux/files/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def minify_json_file(path: Path, dry_run: bool = False) -> bool:
    """
    Minify a single JSON file in-place.
    Returns True if file was modified, False otherwise.
    """
    try:
        original = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[ERROR] Cannot read {path}: {e}")
        return False

    try:
        data = json.loads(original)
    except json.JSONDecodeError:
        print(f"[SKIP] Invalid JSON: {path}")
        return False

    minified = json.dumps(
        data,
        separators=(",", ":"),  # remove spaces
        ensure_ascii=False,  # preserve unicode
    )

    if original.strip() == minified:
        return False  # already minified

    if dry_run:
        print(f"[DRY] Would minify: {path}")
        return True

    try:
        path.write_text(minified, encoding="utf-8")
        print(f"[OK] Minified: {path}")
        return True
    except Exception as e:
        print(f"[ERROR] Cannot write {path}: {e}")
        return False


def main():
    root = Path(".").resolve()
    dry_run = "--dry" in sys.argv

    modified_count = 0
    total_count = 0

    for path in root.rglob("*.json"):
        if path.is_file():
            total_count += 1
            if minify_json_file(path, dry_run=dry_run):
                modified_count += 1

    print("\n--- Summary ---")
    print(f"Total JSON files found: {total_count}")
    print(f"Files modified: {modified_count}")


if __name__ == "__main__":
    main()

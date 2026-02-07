#!/usr/bin/env python3
"""
dedupe_xxhash.py

Usage:
  python dedupe_xxhash.py [path]
  python dedupe_xxhash.py --dry-run [path]
  python dedupe_xxhash.py --restore --dry-run
  python dedupe_xxhash.py --restore

Behavior:
  - Scans 'path' (default current dir) recursively.
  - Ignores symlinks.
  - Groups files by xxh64 hash (with cache keyed by path,size,mtime).
  - Moves one copy per group into ~/dups/ as "<hash>__<basename>".
  - Replaces other copies with symlinks to the stored file.
  - Writes manifest at ~/dups/manifest.json for restore.
  - --restore copies stored files back to original locations and removes stored files and manifest.
"""

import argparse
import json
import os
import shutil
from collections import defaultdict
from pathlib import Path

import xxhash

# Config
CACHE_PATH = Path.home() / ".cache" / "dups_xxhash_cache.json"
DUPS_DIR = Path.home() / "dups"
MANIFEST_PATH = DUPS_DIR / "manifest.json"
READ_CHUNK = 1 << 20  # 1 MiB


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def xxh64_of_path(p: Path):
    h = xxhash.xxh64()
    with p.open("rb") as f:
        while True:
            chunk = f.read(READ_CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_groups(root: Path, cache: dict):
    groups = defaultdict(list)
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            fp = Path(dirpath) / name
            # ignore symlinks
            if fp.is_symlink():
                continue
            # only regular files
            try:
                st = fp.stat()
            except Exception:
                continue
            if not fp.is_file():
                continue
            key = str(fp)
            size = st.st_size
            mtime = st.st_mtime
            cached = cache.get(key)
            if cached and cached.get("size") == size and cached.get("mtime") == mtime:
                h = cached["hash"]
            else:
                try:
                    h = xxh64_of_path(fp)
                except Exception:
                    continue
                cache[key] = {
                    "size": size,
                    "mtime": mtime,
                    "hash": h,
                }
            groups[h].append(fp)
    return groups


def dedupe(root: Path, dry_run=False, force=False):
    cache = load_json(CACHE_PATH) if CACHE_PATH.exists() else {}
    groups = build_groups(root, cache)
    # persist cache early so repeated runs are faster
    save_json(CACHE_PATH, cache)

    DUPS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_json(MANIFEST_PATH) if MANIFEST_PATH.exists() else {}
    changed = False

    for h, paths in groups.items():
        if len(paths) < 2:
            continue
        # sort to have deterministic choice of stored original
        paths_sorted = sorted(paths, key=lambda p: str(p))
        original = paths_sorted[0]
        stored_name = f"{h}__{original.name}"
        stored_path = DUPS_DIR / stored_name

        # If stored file doesn't exist, move the chosen original into dups
        if not stored_path.exists():
            if dry_run:
                print(f"[DRY] move: {original} -> {stored_path}")
            else:
                # ensure parent exists
                stored_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(
                    str(original),
                    str(stored_path),
                )
                print(f"moved: {original} -> {stored_path}")
            changed = True
        # If stored exists but original still exists (rare), remove original before symlink
        elif original.exists():
            if dry_run:
                print(f"[DRY] remove original file before symlink: {original}")
            else:
                original.unlink()
                print(f"removed original file: {original}")

        # For every other duplicate, replace with symlink to stored_path
        for p in paths_sorted[1:]:
            if p.is_symlink():
                # ignore existing symlinks
                continue
            if dry_run:
                print(f"[DRY] symlink: {p} -> {stored_path.resolve()}")
            else:
                # if file exists, remove it (force or not, we remove to create symlink)
                if p.exists():
                    try:
                        p.unlink()
                    except Exception as e:
                        print(f"warning: could not remove {p}: {e}")
                        continue
                p.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(
                    str(stored_path.resolve()),
                    str(p),
                )
                print(f"symlinked: {p} -> {stored_path.resolve()}")
            changed = True

        # update manifest entry
        manifest[str(stored_path)] = {
            "hash": h,
            "originals": [str(p) for p in paths_sorted],
        }

    if not dry_run and changed:
        save_json(MANIFEST_PATH, manifest)
        save_json(CACHE_PATH, cache)
        print(f"manifest written to {MANIFEST_PATH}")
    elif dry_run:
        print("dry-run complete; no changes written.")


def restore(dry_run=False):
    if not MANIFEST_PATH.exists():
        print("No manifest found at ~/dups/manifest.json")
        return
    manifest = load_json(MANIFEST_PATH)
    for stored_str, info in manifest.items():
        stored = Path(stored_str)
        if not stored.exists():
            print(f"stored file missing: {stored}")
            continue
        originals = [Path(p) for p in info.get("originals", [])]
        for orig in originals:
            # if original exists and is not a symlink, skip
            if orig.exists() and not orig.is_symlink():
                print(f"skipping restore for {orig} (exists and not a symlink)")
                continue
            # if it's a symlink, ensure it points to our stored file
            if orig.is_symlink():
                try:
                    target = Path(os.readlink(orig))
                except Exception:
                    print(f"skipping {orig} (broken symlink)")
                    continue
                if target.resolve() != stored.resolve():
                    print(f"skipping {orig} (symlink points elsewhere)")
                    continue
            # restore: remove symlink (if any) and copy stored file back
            if dry_run:
                print(f"[DRY] restore {stored} -> {orig}")
            else:
                if orig.exists() or orig.is_symlink():
                    try:
                        orig.unlink()
                    except Exception as e:
                        print(f"warning: could not remove {orig}: {e}")
                        continue
                orig.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(stored, orig)
                print(f"restored: {orig}")
        # after restoring all originals for this stored file, remove stored file
        if dry_run:
            print(f"[DRY] remove stored file {stored}")
        else:
            try:
                stored.unlink()
                print(f"removed stored file: {stored}")
            except Exception as e:
                print(f"warning: could not remove stored file {stored}: {e}")

    if not dry_run:
        try:
            MANIFEST_PATH.unlink()
            print(f"removed manifest: {MANIFEST_PATH}")
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(
        description="Deduplicate files by moving one copy to ~/dups and symlinking duplicates using xxhash."
    )
    ap.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default current directory)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without making changes",
    )
    ap.add_argument(
        "--restore",
        action="store_true",
        help="Restore files from ~/dups using manifest",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite behavior (not used for safety here)",
    )
    args = ap.parse_args()

    root = Path(args.path).resolve()
    if args.restore:
        restore(dry_run=args.dry_run)
    else:
        dedupe(
            root,
            dry_run=args.dry_run,
            force=args.force,
        )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path


def sanitize_pkg_name(name: str) -> str:
    """
    Convert npm package names to filesystem-safe folder names.
    Examples:
      @babel/core -> babel__core
      lodash-es   -> lodash-es
    """
    name = name.lstrip("@")
    name = name.replace("/", "__")
    name = re.sub(r"[^\w.-]", "_", name)
    return name


def rename_package_dirs(root: Path, dry_run: bool = False) -> None:
    for pkg_json in root.rglob("package.json"):
        pkg_dir = pkg_json.parent

        try:
            with pkg_json.open(encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        pkg_name = data.get("name")
        if not pkg_name:
            continue

        new_name = sanitize_pkg_name(pkg_name)
        new_dir = pkg_dir.parent / new_name

        if pkg_dir.name == new_name:
            continue

        if new_dir.exists():
            print(f"[SKIP] {new_dir} already exists")
            continue

        if dry_run:
            print(f"[DRY] {pkg_dir} -> {new_dir}")
        else:
            print(f"[RENAME] {pkg_dir} -> {new_dir}")
            pkg_dir.rename(new_dir)


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    dry_run = "--dry-run" in sys.argv
    rename_package_dirs(root, dry_run=dry_run)


if __name__ == "__main__":
    main()

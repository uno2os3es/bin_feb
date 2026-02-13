#!/data/data/com.termux/files/usr/bin/env python3

import ast
import shutil
import sys
from pathlib import Path


class SourceCleaner:

    def __init__(self,
                 backup: bool = True,
                 dry_run: bool = False,
                 verbose: bool = False):
        self.backup = backup
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            "files_processed": 0,
            "docstrings_removed": 0,
            "comments_removed": 0,
            "files_with_errors": 0,
        }

    def log(self, msg: str) -> None:
        if self.verbose:
            print(f"[INFO] {msg}")

    # -------------------- DOCSTRINGS --------------------

    def remove_docstrings(self, source: str) -> tuple[str, int]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source, 0

        lines = source.splitlines()
        ranges: list[tuple[int, int]] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
                if node.body and isinstance(node.body[0], ast.Expr):
                    val = node.body[0].value
                    if isinstance(val, ast.Constant) and isinstance(
                            val.value, str):
                        ranges.append(
                            (node.body[0].lineno - 1, node.body[0].end_lineno))

        for start, end in sorted(ranges, reverse=True):
            del lines[start:end]

        return "\n".join(lines) + "\n", len(ranges)

    def remove_comments(self, text: str) -> str:
        cleaned_lines = []
        for line in text.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            comment_index = line.find("#")
            if comment_index != -1:
                line = line[:comment_index]
            if line.strip():
                cleaned_lines.append(line.rstrip())
        return "\n".join(cleaned_lines) + "\n"

    def process_file(self, path: Path) -> None:
        try:
            original = path.read_text(encoding="utf-8")

            no_docs, docs_removed = self.remove_docstrings(original)
            no_comments, comments_removed = self.remove_comments(no_docs)

            if no_comments != original:
                if self.backup and not self.dry_run:
                    shutil.copy2(path, path.with_suffix(".py.bak"))

                if not self.dry_run:
                    path.write_text(no_comments, encoding="utf-8")

            self.stats["files_processed"] += 1
            self.stats["docstrings_removed"] += docs_removed
            self.stats["comments_removed"] += comments_removed

            if self.verbose:
                print(
                    f"✓ {path} | docstrings={docs_removed}, comments={comments_removed}"
                )

        except Exception as exc:
            print(f"✗ {path}: {exc}")
            self.stats["files_with_errors"] += 1

    # -------------------- DIR --------------------

    def process_directory(self, directory: Path) -> None:
        for py in directory.rglob("*.py"):
            if any(
                    p.startswith(".") or p in {"venv", "__pycache__"}
                    for p in py.parts):
                continue
            self.process_file(py)

    # -------------------- STATS --------------------

    def print_stats(self) -> None:
        print("\n" + "=" * 60)
        for k, v in self.stats.items():
            print(f"{k.replace('_', ' ').title()}: {v}")
        print("=" * 60)


# -------------------- CLI --------------------


def main() -> None:
    import argparse

    p = argparse.ArgumentParser("Remove Python docstrings + comments")
    p.add_argument("path", nargs="?", default=".", help="File or directory")
    p.add_argument("-f", "--file", help="Process only one file")
    p.add_argument("--no-backup", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")

    args = p.parse_args()

    cleaner = SourceCleaner(
        backup=not args.no_backup,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    if args.file:
        path = Path(args.file)
        if not path.is_file():
            sys.exit(f"Error: {path} not found")
        cleaner.process_file(path)
    else:
        root = Path(args.path)
        if not root.exists():
            sys.exit(f"Error: {root} not found")
        cleaner.process_directory(root)

    cleaner.print_stats()


if __name__ == "__main__":
    main()

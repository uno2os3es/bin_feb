#!/usr/bin/env python3
import regex as re
import sys
from pathlib import Path


class RegexCommentRemover:
    """Remove C/C++ comments using regex pattern matching."""

    def __init__(self):
        self.pattern = re.compile(r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"', re.DOTALL | re.MULTILINE)

    def remove_comments(self, source: str):
        """Remove C/C++ style comments while preserving strings."""

        def replacer(match):
            s = match.group(0)
            if s.startswith("/"):
                return " " if "\n" not in s else "\n" * s.count("\n")
            else:
                return s

        result = re.sub(self.pattern, replacer, source)
        comment_count = source.count("//") + source.count("/*")
        result_count = result.count("//") + result.count("/*")
        removed = comment_count - result_count

        return result, removed


def process_file(file_path, remover):
    """Process a single C/C++ file to remove comments."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
    except Exception as e:
        print(f"[ERROR] {file_path.name} read: {e}")
        return ("error", file_path, 0)

    try:
        result, comments = remover.remove_comments(code)
    except Exception as e:
        print(f"[ERROR] {file_path.name} processing: {e}")
        import traceback

        traceback.print_exc()
        return ("error", file_path, 0)

    if result != code:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[OK] {file_path.name}: ~{comments} comment markers removed")
            return ("changed", file_path, comments)
        except Exception as e:
            print(f"[ERROR] {file_path.name} write: {e}")
            return ("error", file_path, comments)
    else:
        print(f"[NO CHANGE] {file_path.name}")
        return ("nochange", file_path, 0)


if __name__ == "__main__":
    dir_path = Path.cwd()

    files = [
        p
        for p in dir_path.rglob("*")
        if p.suffix in [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx", ".C", ".H"] and p.is_file()
    ]

    if not files:
        print("No C/C++ files found")
        sys.exit(0)

    print(f"Found {len(files)} C/C++ files")

    init_size = sum(f.stat().st_size for f in files)

    remover = RegexCommentRemover()
    results = []

    for i, fp in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing {fp.name}...")
        result = process_file(fp, remover)
        results.append(result)

    end_size = sum(f.stat().st_size for f in files if f.exists())

    changed = sum(1 for r in results if r[0] == "changed")
    errors = [r for r in results if r[0] == "error"]
    nochg = sum(1 for r in results if r[0] == "nochange")
    total_comments = sum(r[2] for r in results if r[0] == "changed")

    def format_size(size):
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    print(f"\n{'=' * 60}")
    print(f"Files: {len(files)} | Changed: {changed} | Unchanged: {nochg} | Errors: {len(errors)}")
    print(f"Total comment markers removed: ~{total_comments}")
    if errors:
        print("\nErrors in:")
        for _, fn, *_ in errors[:10]:
            print(f"  - {fn}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    print(f"Size reduced: {format_size(init_size - end_size)}")
    print(f"{'=' * 60}")

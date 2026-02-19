#!/usr/bin/env python3
import sys
from multiprocessing import Pool, cpu_count
from pathlib import Path

import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser, Query, QueryCursor

ts_remover = None


class TSCppRemover:
    """Remove comments from C/C++ source files using tree-sitter."""

    def __init__(self):
        self.language = Language(tscpp.language())
        self.parser = Parser(self.language)

        self.query = Query(
            self.language,
            """
            (comment) @comment
        """,
        )

    def remove_comments(self, source: str):
        """Remove comments from C/C++ source code.

        Args:
            source: C/C++ source code as string

        Returns:
            Tuple of (cleaned_code, comment_count)
        """
        source_bytes = source.encode("utf-8")
        tree = self.parser.parse(source_bytes)

        cursor = QueryCursor(self.query)
        matches = cursor.matches(tree.root_node)

        deletions = []
        comment_count = 0

        for pattern_idx, captures_dict in matches:
            for capture_name, nodes in captures_dict.items():
                for node in nodes:
                    start = node.start_byte
                    end = node.end_byte
                    text = source_bytes[start:end].decode("utf-8")

                    stripped = text.strip()
                    if stripped.startswith(
                        (
                            "//!",
                            "///",
                            "/**",
                            "/*!",
                            "///<",
                            "//!<",
                        )
                    ):
                        continue

                    comment_count += 1

                    if end < len(source_bytes) and source_bytes[end : end + 1] == b"\n":
                        end += 1

                    deletions.append((start, end))

        deletions = sorted(set(deletions), reverse=True)

        new_source = bytearray(source_bytes)
        for start, end in deletions:
            del new_source[start:end]

        new_source = bytes(new_source)

        tree = self.parser.parse(new_source)
        if tree.root_node.has_error:
            print(f"Warning: Resulted code has syntax errors, returning original")
            return source, 0

        cleaned = new_source.decode("utf-8")
        cleaned = self._cleanup_blank_lines(cleaned)

        return cleaned, comment_count

    @staticmethod
    def _cleanup_blank_lines(text: str) -> str:
        """Reduce multiple consecutive blank lines to maximum 2."""
        lines = text.splitlines()
        cleaned = []
        blank_streak = 0

        for line in lines:
            if line.strip() == "":
                blank_streak += 1
                if blank_streak <= 2:
                    cleaned.append("")
            else:
                blank_streak = 0
                cleaned.append(line.rstrip())

        result = "\n".join(cleaned)
        if result and not result.endswith("\n"):
            result += "\n"
        return result


def ts_remover_initializer():
    """Initialize TSCppRemover instance for each worker process."""
    global ts_remover
    ts_remover = TSCppRemover()


def process_file(fp):
    """Process a single C/C++ file to remove comments."""
    global ts_remover
    file_path = Path(fp)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"[ERROR] {file_path.name} read: {e}")
        return ("error", file_path, 0)

    try:
        result, comments = ts_remover.remove_comments(code)
    except Exception as e:
        print(f"[ERROR] {file_path.name} processing: {e}")
        return ("error", file_path, 0)

    if comments:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[OK] {file_path.name}: {comments} comments removed")
            return ("changed", file_path, comments)
        except Exception as e:
            print(f"[ERROR] {file_path.name} write: {e}")
            return ("error", file_path, comments)
    else:
        print(f"[NO CHANGE] {file_path.name}")
        return ("nochange", file_path, 0)


if __name__ == "__main__":
    try:
        from fastwalk import walk_files
        from dh import folder_size, format_size
    except ImportError:

        def walk_files(path):
            return [str(p) for p in Path(path).rglob("*")]

        def folder_size(path):
            return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())

        def format_size(size):
            return f"{size / 1024:.2f} KB"

    dir_path = Path.cwd()

    files = [p for p in walk_files(dir_path) if Path(p).suffix in [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx"]]

    if not files:
        print("No C/C++ files found")
        sys.exit(0)

    init_size = folder_size(dir_path)
    nproc = min(cpu_count() or 1, 8)

    with Pool(processes=nproc, initializer=ts_remover_initializer) as pool:
        results = pool.map(process_file, files)

    end_size = folder_size(dir_path)

    changed = sum(1 for r in results if r[0] == "changed")
    errors = [r for r in results if r[0] == "error"]
    nochg = sum(1 for r in results if r[0] == "nochange")

    print(f"\n{'=' * 60}")
    print(f"Files: {len(files)} | Changed: {changed} | Unchanged: {nochg} | Errors: {len(errors)}")
    if errors:
        print("\nErrors in:")
        for _, fn, *_ in errors:
            print(f"  - {fn}")
    print(f"Size reduced: {format_size(init_size - end_size)}")
    print(f"{'=' * 60}")

#!/usr/bin/env python3
import glob
import logging
from multiprocessing import Pool, cpu_count
import os
import sys

try:
    from tree_sitter import Language, Parser
    from tree_sitter_languages import get_language, get_parser
except ImportError:
    print("Error: tree-sitter dependencies not installed.", file=sys.stderr)
    print("Install with: pip install tree-sitter tree-sitter-languages", file=sys.stderr)
    sys.exit(1)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CommentRemover:
    PRESERVE_PATTERNS = [
        "type:",
        "fmt:",
        "noqa",
        "pylint:",
        "flake8:",
        "mypy:",
    ]

    def __init__(self):
        try:
            self.language = get_language("python")
            self.parser = get_parser("python")
        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter: {e}")
            raise

    def should_preserve_comment(self, comment_text: str) -> bool:
        comment_text = comment_text.strip()
        if comment_text.startswith("#!"):
            return True
        return any(pattern in comment_text for pattern in self.PRESERVE_PATTERNS)

    def parse_file(self, filepath: str) -> tuple[str, list[dict]] | None:
        try:
            with open(filepath, encoding="utf-8", errors="replace") as f:
                source_code = f.read()
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return None
        try:
            tree = self.parser.parse(source_code.encode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to parse {filepath}: {e}")
            return None
        return source_code, tree

    def extract_removable_ranges(self, source_code: str, tree) -> list[tuple[int, int]]:
        lines = source_code.split("\n")
        removable_ranges = []
        for line_idx, line in enumerate(lines):
            if "#" not in line:
                continue
            comment_start = line.find("#")
            if comment_start == -1:
                continue
            if self._is_in_string(line, comment_start):
                continue
            comment_text = line[comment_start:]
            if self.should_preserve_comment(comment_text):
                continue
            byte_offset = sum(len(l.encode("utf-8")) + 1 for l in lines[:line_idx])
            byte_offset += len(line[:comment_start].encode("utf-8"))
            end_offset = byte_offset + len(comment_text.encode("utf-8"))
            removable_ranges.append((byte_offset, end_offset))
        removable_ranges.extend(self._extract_docstrings(source_code.encode("utf-8"), tree))
        return self._merge_ranges(sorted(removable_ranges))

    def _is_in_string(self, line: str, pos: int) -> bool:
        in_single = False
        in_double = False
        i = 0
        while i < pos:
            if line[i] == "'" and (i == 0 or line[i - 1] != "\\"):
                in_single = not in_single
            elif line[i] == '"' and (i == 0 or line[i - 1] != "\\"):
                in_double = not in_double
            i += 1
        return in_single or in_double

    def _extract_docstrings(self, source_bytes: bytes, tree) -> list[tuple[int, int]]:
        docstring_ranges = []

        def walk_tree(node, parent_type=None):
            if node.type == "string":
                if parent_type in ("function_definition", "class_definition", "module"):
                    docstring_ranges.append((node.start_byte, node.end_byte))
            for child in node.children:
                child_parent = child.type if child.type in ("function_definition", "class_definition") else parent_type
                walk_tree(child, child_parent)

        walk_tree(tree.root_node)
        return docstring_ranges

    def _merge_ranges(self, ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
        if not ranges:
            return []
        merged = [ranges[0]]
        for current_start, current_end in ranges[1:]:
            last_start, last_end = merged[-1]
            if current_start <= last_end:
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                merged.append((current_start, current_end))
        return merged

    def remove_comments_and_docstrings(self, source_code: str, tree) -> str:
        removable_ranges = self.extract_removable_ranges(source_code, tree)
        if not removable_ranges:
            return source_code
        source_bytes = source_code.encode("utf-8")
        result_bytes = bytearray()
        last_end = 0
        for start, end in removable_ranges:
            result_bytes.extend(source_bytes[last_end:start])
            last_end = end
        result_bytes.extend(source_bytes[last_end:])
        return result_bytes.decode("utf-8", errors="replace")

    def process_file(self, filepath: str) -> bool:
        try:
            parsed = self.parse_file(filepath)
            if parsed is None:
                return False
            source_code, tree = parsed
            cleaned_code = self.remove_comments_and_docstrings(source_code, tree)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(cleaned_code)
            logger.info(f"Processed: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")
            return False


def find_python_files(root_dir: str = ".") -> list[str]:
    python_files = []
    for py_file in glob.glob(os.path.join(root_dir, "**", "*.py"), recursive=True):
        if any(part in py_file for part in ["__pycache__", ".git", ".venv", "venv", ".tox"]):
            continue
        python_files.append(py_file)
    return python_files


def process_files_mp(files: list[str], num_workers: int | None = None) -> tuple[int, int]:
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)
    logger.info(f"Processing {len(files)} files with {num_workers} workers")
    remover = CommentRemover()
    with Pool(num_workers) as pool:
        results = pool.map(remover.process_file, files)
    successful = sum(1 for r in results if r)
    failed = len(results) - successful
    return successful, failed


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove comments and docstrings from Python files recursively using tree-sitter."
    )
    parser.add_argument("directory", nargs="?", default=".", help="Directory to process (default: current directory)")
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=None,
        help=f"Number of worker processes (default: {max(1, cpu_count() - 1)})",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    if not os.path.isdir(args.directory):
        logger.error(f"Directory not found: {args.directory}")
        sys.exit(1)
    python_files = find_python_files(args.directory)
    if not python_files:
        logger.warning(f"No Python files found in {args.directory}")
        sys.exit(0)
    logger.info(f"Found {len(python_files)} Python files")
    successful, failed = process_files_mp(python_files, args.workers)
    logger.info(f"Completed: {successful} successful, {failed} failed")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

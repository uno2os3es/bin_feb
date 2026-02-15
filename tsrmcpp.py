#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

import tree_sitter_cpp as tscpp
from termcolor import cprint
from tree_sitter import Language, Parser


class TSCppRemover:
    def __init__(self):
        self.parser = Parser()
        self.language = Language(tscpp.language())
        self.parser.language = self.language

    def remove_comments(self, source: str) -> tuple[str, int]:
        source_bytes = source.encode("utf-8")
        tree = self.parser.parse(source_bytes)
        root = tree.root_node

        to_delete = []
        removed = 0

        for node in root.children:
            self._collect_comments(node, to_delete, source_bytes)

        # Remove from back to front
        new_source = source_bytes
        for start, end in sorted(to_delete, reverse=True):
            new_source = new_source[:start] + new_source[end:]
            removed += 1

        cleaned = new_source.decode("utf-8")
        cleaned = self._cleanup_blank_lines(cleaned)

        return cleaned, removed

    def _collect_comments(self, node, to_delete, source_bytes):
        if node.type == "comment":
            text = source_bytes[node.start_byte:node.end_byte].decode("utf-8").strip()

            # Skip preprocessor directives
            if text.startswith("#"):
                return

            to_delete.append((node.start_byte, node.end_byte))

        for child in node.children:
            self._collect_comments(child, to_delete, source_bytes)

    @staticmethod
    def _cleanup_blank_lines(text: str) -> str:
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

        return "\n".join(cleaned) + "\n"


def validate_with_treesitter(parser, code: str) -> bool:
    tree = parser.parse(code.encode("utf-8"))
    return not tree.root_node.has_error


def validate_with_clang(file_path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["clang++", "-std=c++20", "-fsyntax-only", str(file_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.returncode == 0, proc.stderr


def process_file(fp):
    file_path = Path(fp)
    init_size = file_path.stat().st_size

    remover = TSCppRemover()
    code = file_path.read_text(encoding="utf-8", errors="ignore")

    result, removed = remover.remove_comments(code)

    if removed == 0:
        cprint(f"[NO CHANGE] {file_path.name}", "blue")
        return

    # Validate with Tree-sitter
    if not validate_with_treesitter(remover.parser, result):
        cprint(f"[TS ERROR] {file_path.name} - changes discarded", "red")
        return

    # Write temporarily for clang validation
    file_path.write_text(result, encoding="utf-8")

    ok, err = validate_with_clang(file_path)
    if not ok:
        cprint(f"[CLANG ERROR] {file_path.name} - reverting", "red")
        file_path.write_text(code, encoding="utf-8")
        return

    end_size = file_path.stat().st_size
    reduced = abs(init_size - end_size)

    cprint(f"[OK] {file_path.name} - removed {removed} comments, reduced {reduced} bytes", "cyan")


if __name__ == "__main__":
    exts = {".cpp", ".cc", ".cxx", ".hpp", ".h", ".hh", ".hxx", ".c"}

    for path in Path().rglob("*"):
        if path.is_file() and path.suffix in exts:
            process_file(path)
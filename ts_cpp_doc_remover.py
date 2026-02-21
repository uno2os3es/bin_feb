#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path

from termcolor import cprint
from tree_sitter import Language, Parser
import tree_sitter_cpp as tscpp


class TSCppRemover:
    def __init__(self):
        self.parser = Parser()
        self.parser.language = Language(tscpp.language())

    def remove_comments(self, source: str) -> str:
        tree = self.parser.parse(source.encode("utf-8"))
        root = tree.root_node
        to_delete = []

        def walk(node):
            if node.type == "comment":
                to_delete.append((node.start_byte, node.end_byte))
            for child in node.children:
                walk(child)

        walk(root)
        new_source = source.encode("utf-8")
        for start, end in sorted(to_delete, reverse=True):
            new_source = new_source[:start] + new_source[end:]
        cleaned = new_source.decode("utf-8")
        return self._cleanup_blank_lines(cleaned)

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


def process_file(fp):
    file_path = Path(fp)
    init_size = file_path.stat().st_size
    remover = TSCppRemover()
    code = file_path.read_text(encoding="utf-8", errors="ignore")
    result = remover.remove_comments(code)
    if len(result) != len(code):
        file_path.write_text(result, encoding="utf-8")
        end_size = file_path.stat().st_size
        reduced = abs(init_size - end_size)
        cprint(f"[OK] {file_path.name} - reduced {reduced} bytes", "cyan")
    else:
        cprint(f"[NO CHANGE] {file_path.name}", "blue")


if __name__ == "__main__":
    exts = {".cpp", ".cc", ".cxx", ".hpp", ".h", ".hh", ".hxx", ".c"}
    for path in Path().rglob("*"):
        if path.is_file() and path.suffix in exts:
            process_file(path)

#!/data/data/com.termux/files/usr/bin/env python3
import ast
import sys
from multiprocessing import Pool
from pathlib import Path

import tree_sitter_python as tspython
from dh import folder_size, format_size
from fastwalk import walk_files
from termcolor import cprint
from tree_sitter import Language, Parser


class TSRemover:
    def __init__(self):
        self.parser = Parser()
        self.parser.language = Language(tspython.language())

    def remove_comments(self, source: str) -> str:
        tree = self.parser.parse(source.encode("utf-8"))
        root = tree.root_node

        to_delete = []

        def walk(node):
            if node.type == "comment":
                to_delete.append((node.start_byte, node.end_byte))

            if node.type == "expression_statement" and len(node.children) == 1:
                child = node.children[0]
                if child.type == "string":
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
    ts_rmc = TSRemover()
    code = file_path.read_text(encoding="utf-8", errors="ignore")
    result = ts_rmc.remove_comments(code)
    if len(result) != len(code):
        try:
            _ = ast.parse(result)
            file_path.write_text(result, encoding="utf-8")
            end_size = file_path.stat().st_size
            sr = int(abs(init_size - end_size))
            cprint(f"[OK] {file_path.name} {format_size(sr)}", "cyan")
            return
        except:
            cprint(f"[ERROR] {file_path.name}", "yellow")
            return
    else:
        cprint(f"[NO CHANGE] {file_path.name}", "blue")
        return


if __name__ == "__main__":
    dir = Path().cwd()
    initsize = folder_size(dir)
    for pth in walk_files(dir):
        path = Path(pth)
        if path.is_file() and path.suffix == ".py":
            process_file(path)
    sres = int(abs(initsize - folder_size(dir)))
    cprint(f"dir size reduced: {format_size(sres)}", "cyan")

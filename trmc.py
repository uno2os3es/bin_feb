#!/data/data/com.termux/files/usr/bin/python

import sys
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser


class TSRemover:
    def __init__(self):
        self.parser = Parser()
        self.parser.language = Language(tspython.language())

    def rmc(self, source: str) -> str:
        tree = self.parser.parse(source.encode("utf-8"))
        root = tree.root_node

        to_delete = []

        def walk(node):
            # Remove comments
            if node.type == "comment":
                to_delete.append((node.start_byte, node.end_byte))

            # Remove docstrings
            if node.type == "expression_statement":
                if len(node.children) == 1:
                    child = node.children[0]
                    if child.type == "string":
                        to_delete.append((node.start_byte, node.end_byte))

            for child in node.children:
                walk(child)

        walk(root)

        # Remove from end to start (important)
        new_source = source.encode("utf-8")
        for start, end in sorted(to_delete, reverse=True):
            new_source = new_source[:start] + new_source[end:]

        cleaned = new_source.decode("utf-8")
        cleaned = self._cleanup_blank_lines(cleaned)
        return cleaned

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


#        return new_source.decode("utf-8")


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    tsrmc = TSRemover()
    code = fn.read_text(encoding="utf-8", errors="ignore")
    result = tsrmc.rmc(code)
    fn.write_text(result)

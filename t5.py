#!/data/data/com.termux/files/usr/bin/env python3
import sys
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, QueryCursor


class TSRemover:
    def __init__(self):
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)
        self.query = self.language.query("""
            (comment) @comment
            (module
              (expression_statement
                (string) @module_docstring))
            (function_definition
              body: (block
                (expression_statement
                  (string) @function_docstring)))
            (class_definition
              body: (block
                (expression_statement
                  (string) @class_docstring)))
        """)

    def remove_comments(self, source: str):

        source_bytes = source.encode("utf-8")

        tree = self.parser.parse(source_bytes)

        cursor = QueryCursor(self.query)

        matches = cursor.matches(tree.root_node)

        deletions = []
        comment_count = 0
        docstring_count = 0
        for pattern_index, captures_dict in matches:
            for capture_name, node_list in captures_dict.items():
                for node in node_list:
                    start = node.start_byte
                    end = node.end_byte

                    text = source_bytes[start:end].decode("utf-8")

                    if capture_name == "comment":
                        stripped = text.strip()
                        if (
                            stripped.startswith("# type:")
                            or stripped.startswith("# type: ignore")
                            or stripped.startswith("# noqa")
                            or stripped.startswith("# pylint:")
                            or stripped.startswith("# mypy:")
                        ):
                            continue
                        comment_count += 1
                    else:
                        docstring_count += 1

                    if end < len(source_bytes) and source_bytes[end : end + 1] == b"\n":
                        end += 1
                    deletions.append((start, end))

        deletions = sorted(set(deletions), reverse=True)

        new_source = source_bytes
        for start, end in deletions:
            new_source = new_source[:start] + new_source[end:]

        cleaned = new_source.decode("utf-8")
        cleaned = self._cleanup_blank_lines(cleaned)
        return cleaned, comment_count, docstring_count

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


if __name__ == "__main__":
    file_path = Path(sys.argv[1])
    ts_rmc = TSRemover()
    code = file_path.read_text(encoding="utf-8", errors="ignore")
    ts_rmc.remove_comments(code)
    result, comments, docstrings = ts_rmc.remove_comments(code)
    file_path.write_text(result, encoding="utf-8")
    print(f"Removed {comments} comments and {docstrings} docstrings from {file_path}")

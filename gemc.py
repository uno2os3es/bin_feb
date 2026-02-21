#!/data/data/com.termux/files/usr/bin/env python3
import ast
import multiprocessing
import os

from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tspython

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)
QUERY_STRING = """
(comment) @comment
(block
  . (expression_statement
    (string)) @docstring)
(module
  . (expression_statement
    (string)) @docstring)
"""


def should_preserve_comment(content):
    content = content.strip()
    return any(content.startswith(p) for p in ["#!", "# type:", "# fmt:"])


def strip_file(file_path):
    cursor = QueryCursor()
    query = Query(PY_LANGUAGE, QUERY_STRING)
    try:
        with open(file_path, encoding="utf-8") as f:
            source_code = f.read()
        source_bytes = bytes(source_code, "utf8")
        tree = parser.parse(source_bytes)
        captures = cursor.captures(query, tree.root_node)
        modifications = []
        for node, tag in captures:
            if tag == "comment":
                comment_text = source_code[node.start_byte : node.end_byte]
                if not should_preserve_comment(comment_text):
                    modifications.append((node.start_byte, node.end_byte, ""))
            elif tag == "docstring":
                parent = node.parent
                if parent and parent.named_child_count == 1:
                    modifications.append((node.start_byte, node.end_byte, "pass"))
                else:
                    modifications.append((node.start_byte, node.end_byte, ""))
        if not modifications:
            return
        modifications.sort(key=lambda x: x[0], reverse=True)
        working_code = source_code
        for start, end, replacement in modifications:
            working_code = working_code[:start] + replacement + working_code[end:]
        try:
            ast.parse(working_code)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(working_code)
        except SyntaxError:
            pass
    except Exception as e:
        print(f"Error in {file_path}: {e}")


def main():
    files = [os.path.join(r, f) for r, _, fs in os.walk(".") for f in fs if f.endswith(".py")]
    if not files:
        return
    print(f"Applying anchored query processing to {len(files)} files...")
    with multiprocessing.get_context("spawn").Pool() as pool:
        pool.map(strip_file, files)
    print("Done.")


if __name__ == "__main__":
    main()

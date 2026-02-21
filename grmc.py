#!/data/data/com.termux/files/usr/bin/env python3
import ast
from multiprocessing import Pool
import os
from pathlib import Path

from dh import folder_size, format_size
from termcolor import cprint
from tree_sitter import Language, Parser
import tree_sitter_python as tspython

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)


def should_preserve_comment(content):
    content = content.strip()
    return content.startswith("#!") or content.startswith("# type:") or content.startswith("# fmt:")


def strip_file(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            source_code = f.read()
        tree = parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node
        to_delete = []
        to_replace_with_pass = []

        def traverse(node):
            if node.type == "comment":
                comment_text = source_code[node.start_byte : node.end_byte]
                if not should_preserve_comment(comment_text):
                    to_delete.append((node.start_byte, node.end_byte))
            elif node.type == "expression_statement":
                child = node.named_children[0] if node.named_children else None
                if child and child.type == "string":
                    parent = node.parent
                    if parent and parent.type == "block":
                        if parent.named_child_count == 1:
                            to_replace_with_pass.append((node.start_byte, node.end_byte))
                        else:
                            to_delete.append((node.start_byte, node.end_byte))
            for child in node.children:
                traverse(child)

        traverse(root_node)
        modifications = [(s, e, "") for s, e in to_delete]
        modifications += [(s, e, "pass") for s, e in to_replace_with_pass]
        modifications.sort(key=lambda x: x[0], reverse=True)
        working_code = source_code
        for start, end, replacement in modifications:
            working_code = working_code[:start] + replacement + working_code[end:]
        try:
            ast.parse(working_code)
        except SyntaxError:
            try:
                ast.parse(working_code.strip())
            except SyntaxError:
                cprint(f"Skipping {file_path}: Resulting code is syntactically invalid.", "blue")
                return
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(working_code)
        cprint(f"[OK] {Path(file_path).name}", "green")
    except Exception as e:
        cprint(f"Error processing {file_path}: {e}", "yellow")


def get_python_files(root):
    for root, _, files in os.walk(root):
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)


def main():
    dir = Path().cwd().resolve()
    initsize = folder_size(dir)
    files = list(get_python_files(dir))
    if not files:
        return
    print(f"Refactoring {len(files)} files...")
    with Pool(8) as pool:
        pool.map(strip_file, files)
    endsize = folder_size(dir)
    cprint(f"{format_size(int(initsize - endsize))}", "cyan")


if __name__ == "__main__":
    main()

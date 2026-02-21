#!/usr/bin/env python3
import multiprocessing as mp
import os
import sys

from tree_sitter import Node, Parser
import tree_sitter_python

_parser = None


def init_worker():
    global _parser
    _parser = Parser()
    _parser.set_language(tree_sitter_python.language())


def is_preserved_comment(source_bytes: bytes, node: Node) -> bool:
    text = source_bytes[node.start_byte : node.end_byte]
    if node.start_byte == 0 and text.startswith(b"#!"):
        return True
    stripped = text.lstrip(b"#").strip()
    return bool(stripped.startswith(b"type:") or stripped.startswith(b"fmt:"))


def collect_nodes_to_remove(source_bytes: bytes, node: Node) -> list[Node]:
    to_remove = []
    if node.type == "comment" and not is_preserved_comment(source_bytes, node):
        to_remove.append(node)
    if node.type == "string":
        parent = node.parent
        if parent and parent.type == "expression_statement":
            grandparent = parent.parent
            if grandparent and grandparent.type == "block":
                for i, child in enumerate(grandparent.children):
                    if child == parent:
                        if i == 0:
                            to_remove.append(node)
                        break
    for child in node.children:
        to_remove.extend(collect_nodes_to_remove(source_bytes, child))
    return to_remove


def process_file(filepath: str) -> tuple[str, bool]:
    global _parser
    try:
        with open(filepath, "rb") as f:
            source_bytes = f.read()
        tree = _parser.parse(source_bytes)
        root = tree.root_node
        to_delete = collect_nodes_to_remove(source_bytes, root)
        if not to_delete:
            return filepath, True
        to_delete.sort(key=lambda n: n.start_byte, reverse=True)
        new_source = bytearray(source_bytes)
        for node in to_delete:
            del new_source[node.start_byte : node.end_byte]
        with open(filepath, "wb") as f:
            f.write(new_source)
        return filepath, True
    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return filepath, False


def main():
    py_files = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    if not py_files:
        print("No Python files found.")
        return
    print(f"Found {len(py_files)} Python files. Processing...")
    pool = mp.Pool(initializer=init_worker)
    results = pool.map(process_file, py_files)
    pool.close()
    pool.join()
    successes = [f for f, ok in results if ok]
    failures = [f for f, ok in results if not ok]
    print(f"Processed {len(successes)} files successfully.")
    if failures:
        print(f"Failed to process {len(failures)} files:")
        for f in failures:
            print(f"  {f}")


if __name__ == "__main__":
    try:
        import tree_sitter
        import tree_sitter_python
    except ImportError:
        print("Error: Missing required package. Please install tree-sitter==0.25.2 and tree-sitter-python==0.25.0")
        sys.exit(1)
    main()

#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path
from multiprocessing import Pool, cpu_count
from tree_sitter import Parser,Language
import tree_sitter_python
import sys
from termcolor import cprint
from dh import folder_size, format_size
EXCLUDE_PREFIXES = (b"#!/", b"# fmt:", b"# type:")

parser = Parser()
parser.language=Language(tree_sitter_python.language())


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


def _collect_docstrings(node, source: bytes, deletions: list):

    def first_named_child(block):
        for child in block.children:
            if child.is_named:
                return child
        return None

    if node.type == "module":
        first = first_named_child(node)
        if first and first.type == "expression_statement":
            string_node = first.child_by_field_name("expression")
            if string_node and string_node.type == "string":
                deletions.append((first.start_byte, first.end_byte))

    if node.type in (
        "class_definition",
        "function_definition",
        "async_function_definition",
    ):
        body = node.child_by_field_name("body")
        if body:
            first = first_named_child(body)
            if first and first.type == "expression_statement":
                string_node = first.child_by_field_name("expression")
                if string_node and string_node.type == "string":
                    deletions.append((first.start_byte, first.end_byte))

    for child in node.children:
        _collect_docstrings(child, source, deletions)


def remove_comments_and_docstrings(path: Path) -> None:
    try:
        source = path.read_bytes()
        tree = parser.parse(source)

        deletions = []

        def walk_comments(node):
            if node.type == "comment":
                text = source[node.start_byte:node.end_byte]
                if not text.lstrip().startswith(EXCLUDE_PREFIXES):
                    deletions.append((node.start_byte, node.end_byte))
            for child in node.children:
                walk_comments(child)

        walk_comments(tree.root_node)

        _collect_docstrings(tree.root_node, source, deletions)

        cleaned = bytearray(source)
        for start, end in sorted(deletions, reverse=True):
            del cleaned[start:end]

        cleaned_text = cleaned.decode("utf-8")
        cleaned_text = _cleanup_blank_lines(cleaned_text)
        cleaned = cleaned_text.encode("utf-8")

        parser.parse(cleaned)

        path.write_bytes(cleaned)
        print(f"[OK] {path.name}")

    except Exception as e:
        cprint(f"[FAIL] {path.name} -> {e}","cyan")


def collect_py_files(root: Path) -> list[Path]:
    if root.is_file() and root.suffix == ".py":
        return [root]
    return [p for p in root.rglob("*.py") if p.is_file()]


def main() -> None:
    root=Path().cwd().resolve()
    files = collect_py_files(root)
    if not files:
        sys.exit("No Python files found")
    init_size=folder_size(root)

    with Pool(cpu_count()) as pool:
        pool.map(remove_comments_and_docstrings, files)


    end_size=folder_size(root)
    difsize=init_size-end_size
    cprint(f"{format_size(difsize)}","cyan")




if __name__ == "__main__":
    main()

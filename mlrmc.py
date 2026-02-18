#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path
from multiprocessing import Pool, cpu_count
from tree_sitter import Parser,Language
import tree_sitter_python
import tree_sitter_rust
import tree_sitter_cpp
import sys

# -------------------------
# Language setup
# -------------------------

LANGUAGES = {
    ".py": tree_sitter_python.language(),
    ".rs": tree_sitter_rust.language(),
    ".cpp": tree_sitter_cpp.language(),
    ".cc": tree_sitter_cpp.language(),
    ".cxx": tree_sitter_cpp.language(),
    ".hpp": tree_sitter_cpp.language(),
    ".h": tree_sitter_cpp.language(),
    ".hh": tree_sitter_cpp.language(),
    ".hxx": tree_sitter_cpp.language(),
}

EXCLUDE_PREFIXES = (b"#!/", b"# fmt:", b"# type:")


def get_parser(lang):
    parser = Parser()
    parser.language=Language(lang)
    return parser


# -------------------------
# Blank-line cleanup
# -------------------------

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


# -------------------------
# Python docstring removal
# -------------------------

def _collect_python_docstrings(node, deletions):
    def first_named_child(block):
        for child in block.children:
            if child.is_named:
                return child
        return None

    if node.type == "module":
        first = first_named_child(node)
        if first and first.type == "expression_statement":
            expr = first.child_by_field_name("expression")
            if expr and expr.type == "string":
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
                expr = first.child_by_field_name("expression")
                if expr and expr.type == "string":
                    deletions.append((first.start_byte, first.end_byte))

    for child in node.children:
        _collect_python_docstrings(child, deletions)


# -------------------------
# Core processor
# -------------------------

def process_file(path: Path) -> None:
    try:
        ext = path.suffix.lower()
        lang = LANGUAGES.get(ext)

        if not lang:
            return

        parser = get_parser(lang)

        source = path.read_bytes()
        tree = parser.parse(source)

        deletions = []

        def walk(node):
            # Remove comments for all languages
            if node.type == "comment":
                text = source[node.start_byte:node.end_byte]

                # Special filtering for Python
                if ext == ".py":
                    if text.lstrip().startswith(EXCLUDE_PREFIXES):
                        return

                deletions.append((node.start_byte, node.end_byte))

            for child in node.children:
                walk(child)

        walk(tree.root_node)

        # Python docstrings only
        if ext == ".py":
            _collect_python_docstrings(tree.root_node, deletions)

        if not deletions:
            return

        cleaned = bytearray(source)

        for start, end in sorted(deletions, reverse=True):
            del cleaned[start:end]

        cleaned_text = cleaned.decode("utf-8")
        cleaned_text = _cleanup_blank_lines(cleaned_text)
        cleaned = cleaned_text.encode("utf-8")

        # Validate parse
        parser.parse(cleaned)

        path.write_bytes(cleaned)
        print(f"[OK] {path}")

    except Exception as e:
        print(f"[FAIL] {path} -> {e}")


# -------------------------
# File collection
# -------------------------

def collect_supported_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in LANGUAGES else []

    return [
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in LANGUAGES
    ]


# -------------------------
# CLI
# -------------------------

def main() -> None:
    root=Path().cwd().resolve()
    files = collect_supported_files(root)
    if not files:
        sys.exit("No supported files found")

    with Pool(cpu_count()) as pool:
        pool.map(process_file, files)


if __name__ == "__main__":
    main()

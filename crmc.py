#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path
from multiprocessing import Pool, cpu_count
from tree_sitter import Parser, Language
import tree_sitter_cpp
import sys

from termcolor import cprint
from dh import folder_size,format_size

EXCLUDE_PREFIXES = (b"#!/",)

parser = Parser()
parser.language=Language(tree_sitter_cpp.language())


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


def remove_comments_cpp(path: Path) -> None:
    try:
        source = path.read_bytes()
        tree = parser.parse(source)

        deletions = []

        def walk(node):
            if node.type == "comment":
                text = source[node.start_byte:node.end_byte]

                # preserve shebang (rare but possible)
                if text.lstrip().startswith(EXCLUDE_PREFIXES):
                    return

                deletions.append((node.start_byte, node.end_byte))

            for child in node.children:
                walk(child)

        walk(tree.root_node)

        if not deletions:
            return

        cleaned = bytearray(source)

        # delete in reverse byte order
        for start, end in sorted(deletions, reverse=True):
            del cleaned[start:end]

        # normalize blank lines
        cleaned_text = cleaned.decode("utf-8")
        cleaned_text = _cleanup_blank_lines(cleaned_text)
        cleaned = cleaned_text.encode("utf-8")

        # validate syntax (Tree-sitter parse)
        parser.parse(cleaned)

        path.write_bytes(cleaned)
        print(f"[OK] {path.name}")

    except Exception as e:
        cprint(f"[FAIL] {path.name} -> {e}","cyan")


def collect_cpp_files(root: Path) -> list[Path]:
    exts = {".cpp", ".cc", ".cxx", ".hpp", ".h", ".hh", ".hxx"}

    if root.is_file() and root.suffix in exts:
        return [root]

    return [p for p in root.rglob("*") if p.is_file() and p.suffix in exts]


def main() -> None:
    root=Path().cwd().resolve()
    init_size=folder_size(root)
    files = collect_cpp_files(root)
    if not files:
        sys.exit("No C++ files found")

    with Pool(cpu_count()) as pool:
        pool.map(remove_comments_cpp, files)
    end_size=folder_size(root)
    difsize=init_size-end_size
    cprint(f"{format_size(difsize)}","cyan")

if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/python

import argparse
import ast
import io
import os
import tokenize
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_EXCLUDES = {".git", "dist", "venv", ".venv"}


def remove_comments_and_docstrings(source: str) -> str:
    """Remove comments and docstrings from Python source code."""

    def visit_node(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and (
            node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str)
        ):
            node.body.pop(0)
        for child in ast.iter_child_nodes(node):
            visit_node(child)

    tree = ast.parse(source)
    visit_node(tree)
    code_without_docstrings = ast.unparse(tree)
    io_obj = io.StringIO(code_without_docstrings)
    out = []
    prev_toktype = tokenize.INDENT
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type, token_string, _, _, _ = tok

        if token_type == tokenize.Whitespace:
            out.append(token_string)
        if token_type == tokenize.COMMENT or (token_type == tokenize.NL and prev_toktype == tokenize.NEWLINE):
            continue
        out.append(token_string)
        prev_toktype = token_type
    return "".join(out)


def process_file(path: str, inplace: bool) -> None:
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
        cleaned = remove_comments_and_docstrings(source)
        if inplace:
            with open(path, "w", encoding="utf-8") as f:
                f.write(cleaned)
        else:
            print(f"--- {path} ---\n{cleaned}\n")
    except Exception as e:
        print(f"Error processing {path}: {e}")


def walk_directory(root: str, excludes: set) -> list[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in excludes]
        for filename in filenames:
            if filename.endswith(".py"):
                files.append(os.path.join(dirpath, filename))
    return files


def main():
    parser = argparse.ArgumentParser(description="Clean Python files by removing comments and docstrings.")
    parser.add_argument("-f", "--file", help="Clean a single file")
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively clean all .py files in current dir",
    )
    parser.add_argument("--inplace", action="store_true", default=True, help="Update files in place")
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=list(DEFAULT_EXCLUDES),
        help="Directories to exclude (default: .git dist venv .venv)",
    )
    args = parser.parse_args()
    targets = []
    if args.file:
        targets.append(args.file)
    elif args.recursive:
        targets.extend(walk_directory(os.getcwd(), set(args.exclude)))
    else:
        parser.error("You must specify either -f FILE or -r")
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_file, path, args.inplace): path for path in targets}
        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()

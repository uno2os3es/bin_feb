#!/data/data/com.termux/files/usr/bin/python
"""
Remove multi-line docstrings from Python files recursively or from a single file.
Handles docstrings in classes, functions, and modules.
"""

import ast
from pathlib import Path
import shutil
import sys

import regex as re


class DocstringRemover:
    """Remove docstrings from Python source code."""

    def __init__(self, backup: bool = True, verbose: bool = False, dry_run: bool = False):
        self.backup = backup
        self.verbose = verbose
        self.dry_run = dry_run
        self.stats = {
            "files_processed": 0,
            "docstrings_removed": 0,
            "files_with_errors": 0,
        }

    def log(self, message: str):
        if self.verbose:
            print(f"[INFO] {message}")

    def find_python_files(self, directory: str = ".") -> list[Path]:
        python_files: list[Path] = []
        path = Path(directory)

        for py_file in path.rglob("*.py"):
            if any(part.startswith(".") or part in {"venv", "__pycache__"} for part in py_file.parts):
                continue
            python_files.append(py_file)

        self.log(f"Found {len(python_files)} Python files")
        return sorted(python_files)

    def remove_docstrings_simple(self, content: str) -> tuple[str, int]:
        removed_count = 0
        lines = content.split("\n")
        result_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if '"""' in line or "'''" in line:
                delimiter = '"""' if '"""' in line else "'''"
                count = line.count(delimiter)

                if count >= 2:
                    first = line.find(delimiter)
                    second = line.find(delimiter, first + 3)
                    before = line[:first].rstrip()

                    if before.endswith(":") or before.strip() == "":
                        result_lines.append(line[:first] + line[second + 3 :])
                        removed_count += 1
                        i += 1
                        continue

                before = line[: line.find(delimiter)].rstrip()

                if before.endswith(":") or before.strip() == "" or "=" not in before:
                    removed_count += 1
                    if before:
                        result_lines.append(before)

                    j = i + 1
                    while j < len(lines):
                        if delimiter in lines[j]:
                            after = lines[j][lines[j].find(delimiter) + 3 :].strip()
                            if after:
                                result_lines.append(after)
                            i = j + 1
                            break
                        j += 1
                    else:
                        i = j
                else:
                    result_lines.append(line)
                    i += 1
            else:
                result_lines.append(line)
                i += 1

        return "\n".join(result_lines), removed_count

    def remove_docstrings_ast(self, content: str) -> tuple[str, int]:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            self.log("AST parse failed, falling back to simple method")
            return self.remove_docstrings_simple(content)

        lines = content.split("\n")
        ranges = self._find_docstring_ranges(tree)

        for start, end in sorted(ranges, reverse=True):
            del lines[start - 1 : end]

        return "\n".join(lines), len(ranges)

    def _find_docstring_ranges(self, node) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []

        for child in ast.walk(node):
            if isinstance(child, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if child.body and isinstance(child.body[0], ast.Expr):
                    value = child.body[0].value
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        if child.body[0].lineno and child.body[0].end_lineno:
                            ranges.append((child.body[0].lineno, child.body[0].end_lineno))

        return ranges

    def _cleanup_blank_lines(self, content: str) -> str:
        content = re.sub(r"\n\n\n+", "\n\n", content)
        return "\n".join(line.rstrip() for line in content.split("\n"))

    def process_file(self, file_path: Path, method: str = "ast") -> tuple[bool, int]:
        try:
            original = file_path.read_text(encoding="utf-8")

            if method == "ast":
                modified, removed = self.remove_docstrings_ast(original)
            else:
                modified, removed = self.remove_docstrings_simple(original)

            modified = self._cleanup_blank_lines(modified)

            if removed > 0 and self.verbose:
                print(f"✓ {file_path}: removed {removed} docstring(s)")

            if not self.dry_run and self.backup and modified != original:
                shutil.copy2(file_path, file_path.with_suffix(".py.bak"))

            if not self.dry_run and modified != original:
                file_path.write_text(modified, encoding="utf-8")

            return True, removed

        except Exception as exc:
            print(f"✗ Error processing {file_path}: {exc}")
            self.stats["files_with_errors"] += 1
            return False, 0

    def process_directory(self, directory: str, method: str) -> dict:
        files = self.find_python_files(directory)

        if not files:
            print("No Python files found")
            return self.stats

        for file_path in files:
            ok, removed = self.process_file(file_path, method)
            if ok:
                self.stats["files_processed"] += 1
                self.stats["docstrings_removed"] += removed

        return self.stats

    def print_stats(self):
        print("\n" + "=" * 60)
        print("STATISTICS")
        print("=" * 60)
        for k, v in self.stats.items():
            print(f"{k.replace('_', ' ').title()}: {v}")
        print("=" * 60)


class DocstringValidator:
    @staticmethod
    def has_syntax_errors(file_path: Path) -> tuple[bool, str | None]:
        try:
            ast.parse(file_path.read_text(encoding="utf-8"))
            return False, None
        except SyntaxError as exc:
            return True, str(exc)

    @staticmethod
    def validate_directory(directory: str) -> dict:
        files = list(Path(directory).rglob("*.py"))
        report = {"total_files": len(files), "valid_files": 0, "invalid_files": 0, "errors": []}

        for f in files:
            has_error, msg = DocstringValidator.has_syntax_errors(f)
            if has_error:
                report["invalid_files"] += 1
                report["errors"].append({"file": str(f), "error": msg})
            else:
                report["valid_files"] += 1

        return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Remove Python docstrings recursively or from a single file")

    parser.add_argument("directory", nargs="?", default=".", help="Directory to process")
    parser.add_argument("-f", "--file", help="Process only a single Python file")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--method", choices=["ast", "simple"], default="ast")
    parser.add_argument("--validate", action="store_true")

    args = parser.parse_args()

    remover = DocstringRemover(
        backup=not args.no_backup,
        verbose=args.verbose,
        dry_run=args.dry_run,
    )

    if args.file:
        file_path = Path(args.file)
        if not file_path.is_file() or file_path.suffix != ".py":
            print(f"Error: '{args.file}' is not a valid Python file")
            sys.exit(1)

        ok, removed = remover.process_file(file_path, args.method)
        if ok:
            remover.stats["files_processed"] = 1
            remover.stats["docstrings_removed"] = removed
    else:
        if not Path(args.directory).is_dir():
            print(f"Error: '{args.directory}' is not a directory")
            sys.exit(1)
        remover.process_directory(args.directory, args.method)

    remover.print_stats()

    if args.validate and not args.file:
        report = DocstringValidator.validate_directory(args.directory)
        print(f"\nValid files: {report['valid_files']}/{report['total_files']}")


if __name__ == "__main__":
    main()

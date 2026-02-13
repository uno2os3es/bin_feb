#!/data/data/com.termux/files/usr/bin/python

import ast
import shutil
import sys
from pathlib import Path

import regex as re


class DocstringRemover:

    def __init__(self, backup: bool = True, verbose: bool = True, dry_run: bool = False):
        self.backup = backup
        self.verbose = verbose
        self.dry_run = dry_run
        self.stats = {
            "files_processed": 0,
            "docstrings_removed": 0,
            "files_with_errors": 0,
        }

    def _is_valid_python(self, content: str) -> tuple[bool, str | None]:
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def log(self, message: str):
        print(f"[INFO] {message}")

    def find_python_files(self, directory: str = ".") -> list[Path]:
        python_files = []
        path = Path(directory)

        for py_file in path.rglob("*.py"):
            if any(part.startswith(".") or part in ["venv", "__pycache__"] for part in py_file.parts):
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
            self.log("Failed to parse file with AST, falling back to simple method")
            return self.remove_docstrings_simple(content)

        lines = content.split("\n")
        docstring_ranges = self._find_docstring_ranges(tree, content)

        # Sort ranges in reverse order to remove from end to start
        for start_line, end_line in sorted(docstring_ranges, reverse=True):
            start_idx = start_line - 1
            end_idx = end_line

            del lines[start_idx:end_idx]

        return "\n".join(lines), len(docstring_ranges)

    def _find_docstring_ranges(self, node, content: str) -> list[tuple[int, int]]:
        docstring_ranges = []
        content.split("\n")

        for child in ast.walk(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(child)

                if docstring:
                    # Find the docstring in the source
                    # Get the first statement which should be the docstring
                    if child.body and isinstance(child.body[0], ast.Expr):
                        if isinstance(child.body[0].value, ast.Constant):
                            docstring_node = child.body[0]
                            start_line = docstring_node.lineno
                            end_line = docstring_node.end_lineno

                            if start_line and end_line:
                                docstring_ranges.append((start_line, end_line))

        return docstring_ranges

    def remove_comments(self, text: str) -> str:
        cleaned_lines = []
        for line in text.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            comment_index = line.find("#")
            if comment_index != -1:
                line = line[:comment_index]
            if line.strip():
                cleaned_lines.append(line.rstrip())
        return "\n".join(cleaned_lines) + "\n"

    def process_file(self, file_path: Path, method: str = "ast") -> tuple[bool, int]:
        try:
            original_content = file_path.read_text(encoding="utf-8")
            original_content = self.remove_comments(original_content)
            if method == "ast":
                modified_content, docstrings_removed = self.remove_docstrings_ast(original_content)
            else:
                modified_content, docstrings_removed = self.remove_docstrings_simple(original_content)

            modified_content = self._cleanup_blank_lines(modified_content)

            if modified_content == original_content:
                return True, 0

            is_valid, error = self._is_valid_python(modified_content)

            if not is_valid:
                print(f"✗ Syntax error after processing {file_path}")
                print("  → Changes discarded")
                print(f"  → Error: {error}")
                self.stats["files_with_errors"] += 1
                return False, 0

            if not self.dry_run and self.backup:
                backup_path = file_path.with_suffix(".py.bak")
                shutil.copy2(file_path, backup_path)
                self.log(f"Backup created: {backup_path}")

            if not self.dry_run:
                file_path.write_text(modified_content, encoding="utf-8")
                self.log(f"File updated: {file_path}")

            print(f"✓ {file_path}: Removed {docstrings_removed} docstring(s)")

            return True, docstrings_removed

        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            self.stats["files_with_errors"] += 1
            return False, 0

    def _cleanup_blank_lines(self, content: str) -> str:
        content = re.sub(r"\n\n\n+", "\n\n", content)

        lines = [line.rstrip() for line in content.split("\n")]

        return "\n".join(lines)

    def process_directory(
        self, directory: str = ".", method: str = "ast", exclude_patterns: list[str] | None = None
    ) -> dict:
        python_files = self.find_python_files(directory)

        if not python_files:
            print("No Python files found")
            return self.stats

        print(f"\nProcessing {len(python_files)} files...")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'NORMAL'}")
        print("-" * 60)

        for file_path in python_files:
            success, removed = self.process_file(file_path, method=method)

            if success:
                self.stats["files_processed"] += 1
                self.stats["docstrings_removed"] += removed

        return self.stats

    def print_stats(self):
        print("\n" + "=" * 60)
        print("STATISTICS")
        print("=" * 60)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Docstrings removed: {self.stats['docstrings_removed']}")
        print(f"Files with errors: {self.stats['files_with_errors']}")
        print("=" * 60)


class DocstringValidator:

    @staticmethod
    def has_syntax_errors(file_path: Path) -> tuple[bool, str | None]:
        try:
            content = file_path.read_text(encoding="utf-8")
            ast.parse(content)
            return False, None
        except SyntaxError as e:
            return True, str(e)

    @staticmethod
    def validate_directory(directory: str = ".") -> dict:
        python_files = list(Path(directory).rglob("*.py"))

        report = {"total_files": len(python_files), "valid_files": 0, "invalid_files": 0, "errors": []}

        for file_path in python_files:
            has_error, error_msg = DocstringValidator.has_syntax_errors(file_path)

            if has_error:
                report["invalid_files"] += 1
                report["errors"].append({"file": str(file_path), "error": error_msg})
            else:
                report["valid_files"] += 1

        return report


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove multi-line docstrings from Python files recursively",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python remove_docstrings.py
  python remove_docstrings.py /path/to/project
  python remove_docstrings.py --dry-run
  python remove_docstrings.py --no-backup
  python remove_docstrings.py -v
  python remove_docstrings.py --validate
  python remove_docstrings.py --method simple
        """,
    )

    parser.add_argument("directory", nargs="?", default=".", help="Directory to process (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without modifying files")
    parser.add_argument("--no-backup", action="store_true", help="Do not create backup files")
    parser.add_argument(
        "--method",
        choices=["ast", "simple"],
        default="ast",
        help="Removal method: ast (default) or simple (regex-based)",
    )
    parser.add_argument("--verbose", action="store_true", help="verbose mode")
    parser.add_argument("--no-cleanup", action="store_true", help="Do not clean up blank lines")

    args = parser.parse_args()

    if not Path(args.directory).is_dir():
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)

    print("╔════════════════════════════════════════════════════════════╗")
    print("║        Python Docstring Removal Tool                       ║")
    print("╚════════════════════════════════════════════════════════════╝")

    remover = DocstringRemover(backup=not args.no_backup, verbose=True, dry_run=args.dry_run)

    stats = remover.process_directory(args.directory, method=args.method)

    remover.print_stats()

    if args.dry_run:
        print("\n✓ Dry run completed. No files were modified.")
    elif stats["docstrings_removed"] > 0:
        print("\n✓ Docstrings removed successfully!")
        if not args.no_backup:
            print("✓ Backup files created with .bak extension")


if __name__ == "__main__":
    main()

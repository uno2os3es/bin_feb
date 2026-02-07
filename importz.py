#!/usr/bin/env python3
import ast
import pathlib
import sys


def is_python_file(path: pathlib.Path) -> bool:
    """Check if a file is likely Python, even without an extension."""
    if path.suffix == ".py":
        return True
    if path.is_file() and not path.suffix:
        try:
            with open(path, encoding="utf-8") as f:
                first_line = f.readline()
                return "python" in first_line  # Detect shebang
        except Exception:
            return False
    return False


def get_imports_from_file(file_path):
    """Parses a file and returns a set of top-level module names."""
    imports = set()
    try:
        with open(file_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports.add(node.module.split(".")[0])
    except (SyntaxError, UnicodeDecodeError):
        pass
    return imports


def main():
    current_dir = pathlib.Path(".")
    output_file = current_dir / "importz.txt"
    all_imports = set()

    # 1. Identify local modules and packages to trim them later
    local_names = {p.stem for p in current_dir.glob("*.py")}
    local_names.update({p.name for p in current_dir.iterdir() if p.is_dir() and (p / "__init__.py").exists()})

    # 2. Get Standard Library names
    # sys.stdlib_module_names is available in Python 3.10+
    std_libs = getattr(sys, "stdlib_module_names", set())

    # 3. Collect imports from all Python files (including extensionless ones)
    for path in current_dir.rglob("*"):
        if is_python_file(path) and path.name != "importz.txt":
            all_imports.update(get_imports_from_file(path))

    # 4. Filter: Trim standard libs, local files, and __future__
    third_party = sorted(
        [imp for imp in all_imports if imp not in std_libs and imp not in local_names and imp != "__future__"]
    )

    # 5. Save results
    if third_party:
        output_file.write_text(
            "\n".join(third_party),
            encoding="utf-8",
        )
        print(f"✅ Saved {len(third_party)} 3rd-party imports to {output_file}")
    else:
        print("ℹ️ No 3rd-party imports found.")


if __name__ == "__main__":
    main()

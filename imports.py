#!/data/data/com.termux/files/usr/bin/env python3

import ast
import importlib.metadata
import importlib.util
import numbers
import os
import pathlib

from dh import STDLIB, get_installed_pkgs


def get_py_files(start_path):
    """Recursively find all .py files in the given directory."""
    return list(pathlib.Path(start_path).rglob("*.py*"))


class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()

    def visit_Import(self, node):
        for name in node.names:
            self.imports.add(name.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.level == 0 and node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)


def find_imports(start_path):
    """Parses files to find unique top-level imports."""
    all_imports = set()
    std_libs = STDLIB

    for py_file in get_py_files(start_path):
        try:
            with open(py_file, encoding="utf-8") as f:
                tree = ast.parse(
                    f.read(),
                    filename=str(py_file),
                )
            visitor = ImportVisitor()
            visitor.visit(tree)
            all_imports.update(visitor.imports)
        except (SyntaxError, UnicodeDecodeError):
            continue

    local_files = {p.stem for p in pathlib.Path(start_path).glob("*.py")}

    return sorted(
        [imp for imp in all_imports if imp not in std_libs and imp not in local_files and imp != "__future__"]
    )


def get_version(module_name):
    """Tries to find a module version using metadata or internal attributes."""
    try:
        return importlib.metadata.version(module_name)
    except importlib.metadata.PackageNotFoundError:
        pass

    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return "Not Installed"

        mod = importlib.import_module(module_name)
        for k, v in mod.__dict__.items():
            if ("version" in k.lower() or "ver" in k.lower()) and isinstance(v, (str, numbers.Number)):
                return str(v)
    except Exception:
        return "Not Installed(unknown)"

    return "Not Installed(NA)"


def main():
    search_path = "."
    output_file = "importz.txt"

    print(f"Scanning directory: {os.path.abspath(search_path)}...")
    modules = find_imports(search_path)

    results = []
    print(f"{'Module':<20} | {'Version':<15}")
    print("-" * 40)

    for mod in modules:
        if mod not in STDLIB:
            ver = get_version(mod)
            line = f"{mod:<20} | {ver:<15}"
            print(line)
            if "Not Installed" in ver:
                results.append(f"{mod}=={ver}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    cleaned = []

    with open(output_file, encoding="utf-8") as fin:
        lines = fin.readlines()
        for line in lines:
            cleaned.append(
                line.rstrip()
                .replace("Not Installed", "")
                .replace("==(NA)", "")
                .replace("==(unknown)", "")
                .replace("==", "")
            )
    pkgz = get_installed_pkgs()
    cleaned = [p for p in cleaned if p not in pkgz]
    if cleaned:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(cleaned))
    else:
        os.remove("importz.txt")

    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()

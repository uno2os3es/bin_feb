#!/usr/bin/env python3
"""
Offline Python import collector for requirements.txt generation.
Recursively scans current dir including compressed archives.
Uses /sdcard/whl/pip.txt for package validation
"""

import ast
import tarfile
import zipfile
from collections import defaultdict
from pathlib import Path

import regex as re
from dh import STDLIB

# Termux shebang patterns
SHEBANG_PATTERNS = [
    r"#!/data/data/com.termux/files/usr/bin/python",
    r"#!/usr/bin/env python",
    r"#! */python",
]

# Compressed file extensions
COMPRESSED_EXTS = {
    ".tar.gz",
    ".tgz",
    ".tar.xz",
    ".tar.bz2",
    ".tar.zst",
    ".zip",
    ".whl",
    ".7z",
}

# Pip packages list path and stdlib path
PIP_LIST_PATH = Path("/sdcard/pip.txt")
KNOWN_PACKAGES = set()
STDLIB_MODULES = STDLIB


def load_known_packages():
    """Load known pip packages from saved list."""
    global KNOWN_PACKAGES
    if PIP_LIST_PATH.exists():
        try:
            with open(PIP_LIST_PATH) as f:
                KNOWN_PACKAGES = {
                    line.strip().split("==")[0].split(">")[0].split("<")
                    [0].lower()
                    for line in f if line.strip()
                }
        except Exception:
            pass


def is_python_file(path):
    """Check if file is Python source (with/without extension or shebang)."""
    path = Path(path)

    # No extension or .py
    if not path.suffix or path.suffix == ".py":
        try:
            with open(
                    path,
                    encoding="utf-8",
                    errors="ignore",
            ) as f:
                first_line = f.readline()
                # Check shebang
                for pattern in SHEBANG_PATTERNS:
                    if re.match(pattern, first_line):
                        return True
                # Check for import-like content
                content = f.read(1024)
                if re.search(
                        r"\bimport\b|\bfrom\b\s+\w",
                        content,
                        re.I,
                ):
                    return True
        except:
            pass
        return False

    return path.suffix == ".py"


def extract_imports_from_ast(code):
    """Extract imports using AST parser."""
    imports = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0].lower())
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0].lower())
    except:
        pass
    return imports


def extract_imports_regex(content):
    """Fallback regex-based import extraction."""
    imports = set()
    # Import patterns
    patterns = [
        r"^\s*import\s+(\w+)",
        r"^\s*from\s+(\w+)\s+import",
        r"^\s*import\s+\w+\s+as\s+\w+",
    ]
    for line in content.splitlines():
        for pattern in patterns:
            match = re.search(pattern, line, re.I)
            if match:
                pkg = match.group(1).split(".")[0].lower()
                imports.add(pkg)
    return imports


def get_imports_from_file(file_path):
    """Extract imports from single Python file."""
    try:
        with open(
                file_path,
                encoding="utf-8",
                errors="ignore",
        ) as f:
            content = f.read()

        # Try AST first, then regex
        imports = extract_imports_from_ast(content)
        if not imports:
            imports = extract_imports_regex(content)

        return {imp for imp in imports if imp and imp != "from"}
    except:
        return set()


def handle_compressed_file(archive_path):
    """Extract and scan Python files from compressed archives."""
    all_imports = defaultdict(int)

    path = Path(archive_path)

    try:
        # .zip and .whl
        if path.suffix in {".zip", ".whl"}:
            with zipfile.ZipFile(path, "r") as zf:
                for name in zf.namelist():
                    if is_python_file(name):
                        content = zf.read(name).decode(
                            "utf-8",
                            errors="ignore",
                        )
                        imports = extract_imports_from_ast(
                            content) or extract_imports_regex(content)
                        for imp in imports:
                            all_imports[imp] += 1

        # .tar.gz, .tgz
        elif path.suffix in {".tar.gz", ".tgz"}:
            with tarfile.open(path, "r:gz") as tf:
                for member in tf.getmembers():
                    if is_python_file(member.name) and not member.isdir():
                        f = tf.extractfile(member)
                        if f:
                            content = f.read().decode(
                                "utf-8",
                                errors="ignore",
                            )
                            imports = extract_imports_from_ast(
                                content) or extract_imports_regex(content)
                            for imp in imports:
                                all_imports[imp] += 1

        # .tar.xz
        elif path.suffix == ".tar.xz":
            with tarfile.open(path, "r:xz") as tf:
                for member in tf.getmembers():
                    if is_python_file(member.name) and not member.isdir():
                        f = tf.extractfile(member)
                        if f:
                            content = f.read().decode(
                                "utf-8",
                                errors="ignore",
                            )
                            imports = extract_imports_from_ast(
                                content) or extract_imports_regex(content)
                            for imp in imports:
                                all_imports[imp] += 1

        # .tar.bz2
        elif path.suffix == ".tar.bz2":
            with tarfile.open(path, "r:bz2") as tf:
                for member in tf.getmembers():
                    if is_python_file(member.name) and not member.isdir():
                        f = tf.extractfile(member)
                        if f:
                            content = f.read().decode(
                                "utf-8",
                                errors="ignore",
                            )
                            imports = extract_imports_from_ast(
                                content) or extract_imports_regex(content)
                            for imp in imports:
                                all_imports[imp] += 1

        # .tar.zst (requires zstd)
        elif path.suffix == ".tar.zst":
            try:
                import zstandard as zstd

                dctx = zstd.ZstdDecompressor()
                with (
                        open(path, "rb") as f,
                        dctx.stream_reader(f) as reader,
                        tarfile.open(
                            fileobj=reader,
                            mode="r",
                        ) as tf,
                ):
                    for member in tf.getmembers():
                        if is_python_file(member.name) and not member.isdir():
                            f = tf.extractfile(member)
                            if f:
                                content = f.read().decode(
                                    "utf-8",
                                    errors="ignore",
                                )
                                imports = extract_imports_from_ast(
                                    content) or extract_imports_regex(content)
                                for imp in imports:
                                    all_imports[imp] += 1
            except ImportError:
                pass

        # .7z (requires 7z command)
        elif path.suffix == ".7z":
            try:
                import subprocess

                result = subprocess.run(
                    ["7z", "l", str(path)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                for line in result.stdout.splitlines():
                    if ".py" in line or ("python" in line.lower()
                                         and "bin" not in line.lower()):
                        pass  # Would need extraction, skipping for offline
            except:
                pass

    except Exception:
        pass

    return dict(all_imports)


def walk_directory(root_path):
    """Recursively walk directory and collect imports."""
    all_imports = defaultdict(int)

    root = Path(root_path)

    for path in root.rglob("*"):
        try:
            # Regular Python files
            if path.is_file() and is_python_file(path):
                imports = get_imports_from_file(path)
                for imp in imports:
                    all_imports[imp] += 1

            # Compressed archives
            elif path.is_file() and path.suffix.lower() in COMPRESSED_EXTS:
                archive_imports = handle_compressed_file(path)
                for (
                        imp,
                        count,
                ) in archive_imports.items():
                    all_imports[imp] += count

        except Exception:
            continue

    return dict(all_imports)


def generate_requirements(imports_count):
    """Generate requirements.txt filtered by known packages and excluding stdlib."""
    filtered = {
        pkg: count
        for pkg, count in imports_count.items()
        if pkg in KNOWN_PACKAGES and pkg not in STDLIB_MODULES
    }

    # Sort by frequency
    sorted_imports = sorted(
        filtered.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    with open("requirements.txt", "w") as f:
        for pkg, count in sorted_imports:
            # Normalize package name (common fixes)
            norm_pkg = pkg.replace("_", "-")
            if norm_pkg in {
                    "numpy",
                    "pandas",
                    "matplotlib",
            }:
                f.write(f"{norm_pkg}\n")
            else:
                f.write(f"{norm_pkg}\n")

    print(
        f"Generated requirements.txt with {len(sorted_imports)} packages (stdlib excluded)"
    )
    print("Top 10 most used packages:")
    for pkg, count in sorted_imports[:10]:
        print(f"  {pkg}: {count} files")


def main():
    load_known_packages()
    print(f"Loaded {len(KNOWN_PACKAGES)} packages from pip.txt")

    print("Scanning current directory...")
    imports_count = walk_directory(".")

    print(
        f"Found {sum(imports_count.values())} total imports across {len(imports_count)} packages"
    )

    generate_requirements(imports_count)


if __name__ == "__main__":
    main()

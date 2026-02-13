#!/usr/bin/env python3
import ast
import importlib.metadata
import importlib.util
import pathlib
import sys

# Mapping of { import_name : pip_install_name }
PACKAGE_MAPPING = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "google": "google-cloud-storage",  # Can vary based on specific GCP lib
    "dotenv": "python-dotenv",
    "bs4": "beautifulsoup4",
    "fitz": "pymupdf",
    "skimage": "scikit-image",
    "telegram": "python-telegram-bot",
    "dateutil": "python-dateutil",
    "git": "GitPython",
    "pydantic_core": "pydantic",
    "jwt": "PyJWT",
    "OpenGL": "PyOpenGL",
}


def is_python_file(path: pathlib.Path) -> bool:
    """Check if a file is likely Python, even without an extension."""
    if path.suffix == ".py":
        return True
    if path.is_file() and not path.suffix:
        try:
            with open(path, encoding="utf-8") as f:
                first_line = f.readline()
                return "python" in first_line
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
            elif isinstance(
                    node, ast.ImportFrom) and node.level == 0 and node.module:
                imports.add(node.module.split(".")[0])
    except (SyntaxError, UnicodeDecodeError):
        pass
    return imports


def check_status(module_name):
    """Returns True if module is installed, False otherwise."""
    # Check via metadata
    try:
        importlib.metadata.distribution(module_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        # Check if it exists in path (for modules that don't match package name)
        spec = importlib.util.find_spec(module_name)
        return spec is not None


def main():
    current_dir = pathlib.Path(".")
    output_file = current_dir / "importz.txt"
    pip_script = current_dir / "install_deps.sh"

    all_imports = set()

    # 1. Local discovery
    local_names = {p.stem for p in current_dir.glob("*.py")}
    local_names.update({
        p.name
        for p in current_dir.iterdir()
        if p.is_dir() and (p / "__init__.py").exists()
    })

    # 2. Stdlib discovery
    std_libs = getattr(sys, "stdlib_module_names", set())

    # 3. Collection
    for path in current_dir.rglob("*"):
        if is_python_file(path) and path.name not in [
                "importz.txt",
                "install_deps.sh",
        ]:
            all_imports.update(get_imports_from_file(path))

    # 4. Filtering & Mapping
    third_party = [
        imp for imp in all_imports if imp not in std_libs
        and imp not in local_names and imp != "__future__"
    ]

    missing_for_pip = []
    already_installed = []

    for imp in sorted(third_party):
        if check_status(imp):
            already_installed.append(imp)
        else:
            # Map to the correct pip name if an alias exists
            pip_name = PACKAGE_MAPPING.get(imp, imp)
            missing_for_pip.append(pip_name)

    # 5. Output
    if third_party:
        output_file.write_text(
            "\n".join(sorted(third_party)),
            encoding="utf-8",
        )
        print(f"✅ Found {len(third_party)} 3rd-party dependencies.")

        if already_installed:
            print(f"📦 Already installed: {', '.join(already_installed)}")

        if missing_for_pip:
            install_cmd = f"pip install {' '.join(missing_for_pip)}"
            pip_script.write_text(
                f"#!/bin/sh\n{install_cmd}\n",
                encoding="utf-8",
            )
            pip_script.chmod(pip_script.stat().st_mode | 0o111)
            print(f"⚠️  Missing: {', '.join(missing_for_pip)}")
            print(f"🚀 Run this to install missing: ./{pip_script.name}")
        else:
            if pip_script.exists():
                pip_script.unlink()
            print("✨ Environment is fully satisfied!")
    else:
        print("ℹ️ No 3rd-party imports found.")


if __name__ == "__main__":
    main()

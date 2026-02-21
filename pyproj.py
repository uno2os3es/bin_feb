#!/data/data/com.termux/files/usr/bin/env python3
"""
Script to create a template Python project structure.
Usage: python create_project.py <package_name>
"""

from pathlib import Path
import sys


def create_python_project(pkg_name):
    """
    Create a template Python project structure in the current directory.
    Args:
        pkg_name (str): Name of the Python package
    """
    # Get current working directory
    current_dir = Path.cwd()
    print(f"Creating Python project '{pkg_name}' in {current_dir}")
    # Create src directory and package directory
    src_dir = current_dir / "src"
    pkg_dir = src_dir / pkg_name
    # Create directories
    pkg_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created directory: {pkg_dir}")
    # Create __init__.py
    init_file = pkg_dir / "__init__.py"
    init_file.touch()
    print(f"✓ Created file: {init_file}")
    # Create README.md
    readme_file = current_dir / "README.md"
    readme_content = f"""# {pkg_name}
## Description
A Python package named {pkg_name}.
## Installation
```bash
pip install -e .
```
Usage
```python
import {pkg_name}
```
License
MIT License
"""
    readme_file.write_text(readme_content)
    print(f"✓ Created file: {readme_file}")
    # Create LICENSE.MIT
    license_file = current_dir / "LICENSE.MIT"
    license_content = """MIT License
"""
    license_file.write_text(license_content)
    print(f"✓ Created file: {license_file}")
    # Create pyproject.toml
    pyproject_file = current_dir / "pyproject.toml"
    pyproject_content = f"""[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
[project]
name = "{pkg_name}"
version = "0.1.0"
description = "A Python package named {pkg_name}"
readme = "README.md"
authors = [
{{name = "Your Name", email = "your.email@example.com"}},
]
license = {{text = "MIT"}}
classifiers = [
"Programming Language :: Python :: 3",
"License :: OSI Approved :: MIT License",
"Operating System :: OS Independent",
]
requires-python = ">=3.7"
[project.urls]
Homepage = "https://github.com/yourusername/{pkg_name}"
Issues = "https://github.com/yourusername/{pkg_name}/issues"
[tool.setuptools.packages.find]
where = ["src"]
"""
    pyproject_file.write_text(pyproject_content)
    print(f"✓ Created file: {pyproject_file}")
    print("\n✓ Project template created successfully!")
    print("\nNext steps:")
    print(f"  1. cd {current_dir}")
    print("  2. Update pyproject.toml with your information")
    print(f"  3. Start coding in src/{pkg_name}/")


def main():
    # Check if package name is provided via command line
    if len(sys.argv) != 2:
        print("Error: Package name is required")
        print("Usage: python create_project.py <package_name>")
        sys.exit * (1)
    pkg = sys.argv[1]
    create_python_project(pkg)


if __name__ == "__main__":
    main()

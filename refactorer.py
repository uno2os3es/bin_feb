#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path

# Ensure the output directory exists
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)
# Files to write refactored code to
func_file = output_dir / "func.py"
classes_file = output_dir / "classes.py"
const_file = output_dir / "const.py"
init_file = output_dir / "__init__.py"
# Clear previous content
for file in [
    func_file,
    classes_file,
    const_file,
    init_file,
]:
    if file.exists():
        file.unlink()

# Helper function to check if a node is a constant (simple assignment)


def is_constant(node):
    return isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets)


# Helper function to write to files


def write_to_file(file_path, content) -> None:
    with Path(file_path).open("a", encoding="utf-8") as f:
        f.write(content + "\n\n")


# Traverse all Python files in the current directory recursively
for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".py") and not file.startswith("output"):
            file_path = Path(root) / file
            with Path(file_path).open(encoding="utf-8") as f:
                content = f.read()
            # Parse the content
            tree = ast.parse(content)
            # Iterate over top-level nodes
            for node in ast.walk(tree):
                # Handle top-level functions
                if isinstance(node, ast.FunctionDef):
                    # Extract the function code
                    func_code = ast.get_source(tree, node)
                    write_to_file(func_file, func_code)
                # Handle top-level classes
                elif isinstance(node, ast.ClassDef):
                    # Extract the class code
                    class_code = ast.get_source(tree, node)
                    write_to_file(classes_file, class_code)
                # Handle constants (simple assignments)
                elif is_constant(node):
                    # Extract the constant code
                    const_code = ast.get_source(tree, node)
                    write_to_file(const_file, const_code)
# Generate __init__.py
with Path(init_file).open("w", encoding="utf-8") as f:
    f.write("from .func import *\n")
    f.write("from .classes import *\n")
    f.write("from .const import *\n")
# Read the generated files for verification
func_content = func_file.read_text() if func_file.exists() else ""
classes_content = classes_file.read_text() if classes_file.exists() else ""
const_content = const_file.read_text() if const_file.exists() else ""
init_content = init_file.read_text() if init_file.exists() else ""
func_content, classes_content, const_content, init_content

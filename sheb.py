#!/data/data/com.termux/files/usr/bin/python3
import os

TARGET_SHEBANG = "#!/data/data/com.termux/files/usr/bin/python"


def is_python_file(filepath):
    # Skip empty files or __init__ files
    if os.path.getsize(filepath) == 0 or filepath.endswith("__init__.py"):
        return False

    # Check if the file has a .py extension
    if filepath.endswith(".py"):
        return True

    # For files without extension, check if they contain Python code or a shebang
    try:
        with open(filepath) as f:
            first_line = f.readline().strip()
            # Check for shebang or common Python file markers
            if first_line.startswith("#!") and "python" in first_line:
                return True
            # Check for common Python file markers (e.g., encoding, import, #noqa)
            if first_line.startswith("#") and ("python" in first_line
                                               or "encoding" in first_line
                                               or "noqa" in first_line):
                return True
            # Check if the first non-comment line is an import statement
            f.seek(0)
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line.startswith(("import ", "from "))
            return False
    except (OSError, UnicodeDecodeError):
        return False


def process_file(filepath):
    with open(filepath, "r+") as f:
        lines = f.readlines()

        # Skip if the file is empty
        if not lines:
            return

        # Check if the first line is a shebang
        if lines and lines[0].startswith("#!"):
            # Replace the shebang
            lines[0] = TARGET_SHEBANG + "\n"
            # Ensure there's a blank line after the shebang
            if len(lines) > 1 and lines[1].strip() != "":
                lines.insert(1, "\n")
        else:
            # Only add shebang if the file contains Python code
            has_python_code = any(line.strip().startswith((
                "import ",
                "from ",
                "def ",
                "class ",
            )) for line in lines)
            if has_python_code:
                lines.insert(0, TARGET_SHEBANG + "\n")
                lines.insert(1, "\n")

        # Write the modified content back to the file
        f.seek(0)
        f.writelines(lines)
        f.truncate()

    # Make the file executable if it's in a 'bin' directory
    if "bin" in filepath.split(os.sep):
        os.chmod(filepath, 0o755)


def traverse_directory(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            if is_python_file(filepath):
                process_file(filepath)


#                print(os.path.relpath(filepath))

if __name__ == "__main__":
    traverse_directory(os.getcwd())

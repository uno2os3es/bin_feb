#!/data/data/com.termux/files/usr/bin/env python3
import os

TARGET_SHEBANG = "#!/data/data/com.termux/files/usr/bin/python"


def is_python_file(filepath):
    if os.path.getsize(filepath) == 0 or filepath.endswith("__init__.py"):
        return False

    if filepath.endswith(".py"):
        return True

    try:
        with open(filepath) as f:
            first_line = f.readline().strip()
            if first_line.startswith("#!") and "python" in first_line:
                return True
            # Check for common Python file markers (e.g., encoding, import, #noqa)
            if first_line.startswith("#") and (
                "python" in first_line or "encoding" in first_line or "noqa" in first_line
            ):
                return True
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

        if not lines:
            return

        if lines and lines[0].startswith("#!"):
            lines[0] = TARGET_SHEBANG + "\n"
            if len(lines) > 1 and lines[1].strip() != "":
                lines.insert(1, "\n")
        else:
            has_python_code = any(
                line.strip().startswith(
                    (
                        "import ",
                        "from ",
                        "def ",
                        "class ",
                    )
                )
                for line in lines
            )
            if has_python_code:
                lines.insert(0, TARGET_SHEBANG + "\n")
                lines.insert(1, "\n")

        f.seek(0)
        f.writelines(lines)
        f.truncate()

    if "bin" in filepath.split(os.sep):
        os.chmod(filepath, 0o755)


def traverse_directory(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            if is_python_file(filepath):
                process_file(filepath)


if __name__ == "__main__":
    traverse_directory(os.getcwd())

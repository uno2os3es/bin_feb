#!/data/data/com.termux/files/usr/bin/python
import os
import subprocess
import sys

TERMUX_PYTHON = "#!/data/data/com.termux/files/usr/bin/python\n"
TERMUX_BASH = "#!/data/data/com.termux/files/usr/bin/bash\n"


def get_clipboard():
    try:
        return subprocess.check_output(["termux-clipboard-get"], text=True)
    except subprocess.CalledProcessError:
        print(
            "Error: failed to get clipboard content",
            file=sys.stderr,
        )
        sys.exit(1)


def detect_shebang(content: str) -> str | None:
    stripped = content.lstrip()

    # If content already has a shebang, do nothing
    if stripped.startswith("#!"):
        return None

    # Simple heuristics
    if "import " in content or "def " in content or stripped.startswith(
            "python"):
        return TERMUX_PYTHON

    if stripped.startswith((
            "echo ",
            "cd ",
            "export ",
            "set ",
            "if ",
            "for ",
            "#!/bin/sh",
    )):
        return TERMUX_BASH

    return None


def create_symlink(out_file):
    base_name = os.path.basename(out_file)
    name_without_ext, ext = os.path.splitext(base_name)

    # Create symlink only if there is an extension
    if ext and os.path.abspath(os.getcwd()) == os.path.abspath(
            os.path.expanduser("~/bin")):
        symlink_path = os.path.join(
            os.path.dirname(out_file),
            name_without_ext,
        )
        try:
            os.symlink(out_file, symlink_path)
            print(f"Symlink created: {symlink_path} -> {out_file}")
        except FileExistsError:
            print(f"Symlink already exists: {symlink_path}")
        except Exception as e:
            print(
                f"Error creating symlink: {e}",
                file=sys.stderr,
            )
    if ext and os.path.abspath(os.getcwd()) == os.path.abspath(
            os.path.expanduser("~/bashbin")):
        symlink_path = os.path.join(
            os.path.dirname(out_file),
            name_without_ext,
        )
        try:
            os.symlink(out_file, symlink_path)
            print(f"Symlink created: {symlink_path} -> {out_file}")
        except FileExistsError:
            print(f"Symlink already exists: {symlink_path}")
        except Exception as e:
            print(
                f"Error creating symlink: {e}",
                file=sys.stderr,
            )


def main():
    if len(sys.argv) != 2:
        print(
            f"Usage: {sys.argv[0]} <output-file>",
            file=sys.stderr,
        )
        sys.exit(1)

    out_file = sys.argv[1]
    clipboard = get_clipboard()

    cwd = os.path.abspath(os.getcwd())
    bin_dir = os.path.abspath(os.path.expanduser("~/bin"))
    bin_dir2 = os.path.abspath(os.path.expanduser("~/bashbin"))

    final_content = clipboard

    if cwd == bin_dir:
        shebang = detect_shebang(clipboard)
        if shebang:
            final_content = shebang + clipboard

    with open(out_file, "w") as f:
        f.write(final_content)

    # Make executable only in ~/bin
    if cwd == bin_dir:
        os.chmod(out_file, 0o755)
    if cwd == bin_dir2:
        os.chmod(out_file, 0o755)

    # Create symlink if the output file has an extension
    create_symlink(out_file)


if __name__ == "__main__":
    main()

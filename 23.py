#!/data/data/com.termux/files/usr/bin/env python3
from multiprocessing import Lock, Pool
import os
from pathlib import Path
import subprocess
import sys

from fastwalk import walk_files

# Global lock for printing to avoid interleaved output from processes
print_lock = Lock()


def is_python_file(path: Path) -> bool:
    """Determines if a file is a Python file.
    Criteria: Ends in .py OR has a python shebang.
    """
    if path.suffix == ".py":
        return True

    # Check for extensionless executable python scripts
    if path.suffix == "":
        try:
            # Read only the first 64 bytes to check shebang
            with open(path, "rb") as f:
                head = f.read(64)
                # Look for standard shebangs like #!/usr/bin/env python or #!/usr/bin/python
                if b"python" in head and b"#!" in head:
                    return True
        except Exception:
            return False
    return False


def run_command(cmd):
    """Runs a subprocess command and returns (returncode, stdout, stderr)."""
    try:
        # We set force-exclude so ruff doesn't format files unrelated to the project context
        # if they happen to be in the list (though we are scanning current dir).
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return (
            result.returncode,
            result.stdout,
            result.stderr,
        )
    except Exception as e:
        return -1, "", str(e)


def process_file(file_path) -> None:
    """Worker function to process a single file.
    1. Run ruff check (fixes)
    2. Run ruff format (styling).
    """
    print(f"[OK] {file_path.name}")
    check_cmd = [
        "ruff",
        "check",
        "--fix",
        "--unsafe-fixes",
        "--line-length",
        "88",
        "--quiet",  # We handle output manually
        str(file_path),
    ]

    rc_check, out_check, err_check = run_command(check_cmd)
    format_cmd = [
        "ruff",
        "format",
        "--config",
        "/data/data/com.termux/files/home/.config/ruff/ruff.toml",
        str(file_path),
    ]

    rc_fmt, _out_fmt, err_fmt = run_command(format_cmd)

    output = []

    if rc_check != 0 or err_check.strip():
        output.append(f"--- Issues fixing {path.name} ---")
        if err_check.strip():
            output.append(err_check.strip())
        if out_check.strip():
            output.append(out_check.strip())

    # If format failed (rare, usually syntax error)
    if rc_fmt != 0 or err_fmt.strip():
        output.append(f"--- Issues formatting {file_path.name} ---")
        if err_fmt.strip():
            output.append(err_fmt.strip())

    if output:
        with print_lock:
            print("\n".join(output))
            sys.stdout.flush()


def get_all_files(root_dir):
    """Recursively finds all python files."""
    py_files = []
    for pth in walk_files(root_dir):
        path = Path(pth)
        if path.is_file() and is_python_file(path):
            py_files.append(path)
    return py_files


def main() -> None:
    # Check if ruff is installed
    try:
        subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            check=True,
        )
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
    ):
        print("Error: 'ruff' is not installed or not in PATH.")
        print("Please run: pip install ruff")
        sys.exit(1)

    root_dir = os.getcwd()
    files = get_all_files(root_dir)

    if not files:
        print("no file found.")
        return
    pool = Pool(8)
    for f in files:
        pool.apply_async(process_file, ((f),))
    pool.close()
    pool.join()


if __name__ == "__main__":
    main()

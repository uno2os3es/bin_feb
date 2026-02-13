#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile


def fold_content_pure(fname, width=35):
    content = ""
    with open(fname, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    lines = content.splitlines()
    folded_lines = []

    for line in lines:
        while len(line) > width:
            folded_lines.append(line[:width])
            line = line[width:]
        if line:
            folded_lines.append(line)

    #    return '\n'.join(folded_lines) + '\n'
    with open(fname, "w") as fo:
        for line in folded_lines:
            fo.write(line + "\n")

    print(f"{fname} updated.")


def fold_file_inplace(filename):
    """Fold file content to 45 columns with spaces, then overwrite the original file."""
    if not os.path.exists(filename):
        print(
            f"Error: File '{filename}' not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Read original content to a temp file first (safer approach)
    with open(filename, encoding="utf-8") as f:
        original_content = f.read()

    # Write to temp file using fold command
    with tempfile.NamedTemporaryFile(
        mode="w+",
        suffix=".tmp",
        delete=False,
        encoding="utf-8",
    ) as temp_f:
        temp_filename = temp_f.name
        temp_f.write(original_content)
        temp_f.flush()

        # Run fold on temp file and capture output
        result = subprocess.run(
            [
                "fold",
                "-w",
                "30",
                "-s",
                temp_filename,
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if result.returncode != 0:
            print(
                f"Error running fold: {result.stderr}",
                file=sys.stderr,
            )
            os.unlink(temp_filename)
            sys.exit(1)

        # Overwrite original file with folded content
        with open(filename, "w", encoding="utf-8") as original_f:
            original_f.write(result.stdout)

    # Clean up temp file
    os.unlink(temp_filename)
    print(f"Successfully folded '{filename}' in place.")


if __name__ == "__main__":
    #    fold_content_pure(sys.argv[1])
    fold_file_inplace(sys.argv[1])

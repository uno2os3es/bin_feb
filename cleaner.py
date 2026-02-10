#!/usr/bin/env python3
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import regex as re
from fastwalk import walk_files


def clean_log(path):
    """Clean tmux artifacts while preserving newlines and line structure."""
    print(f"[] {path}")
    # Comprehensive ANSI + tmux escape sequences [web:12][web:33]
    ansi_tmux_re = re.compile(
        rb"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|" rb"\x08|\x0C|\x0F|\x18|\x1C|" rb"\(\d+[a-z]\(B|\(0[Bqtxl]\(B"
    )

    # Tmux status lines / artifacts [web:31]
    status_re = re.compile(
        rb"\b\d{4}[MGB]\b|"
        rb"\d{3,4}\s+\([^\)]+\)|"
        rb"\[\^\]\(B\(0l\(B<\(0q\(B\s*\d+|"
        rb"\~\\/[^\r\n]*?\s+\$|"
        rb"\(0mqq\(B\s+\d+M\s*/\s*\d+G"
    )
    try:
        with open(path, "rb") as f:
            content = f.read()

        # Remove status lines first (multi-line safe)
        content = status_re.sub(b"", content)

        # Remove ANSI/tmux sequences
        content = ansi_tmux_re.sub(b"", content)

        # Decode preserving newlines, remove only destructive controls
        text = content.decode("utf-8", errors="replace")

        # Keep ALL newlines, tabs, spaces - remove only destructive controls
        # (BEL, VT, FF, etc. but NEVER touch \n, \r, \t, space)
        cleaned_lines = []
        for line in text.splitlines(keepends=True):  # keepends=True preserves \n
            # Remove only specific destructive controls from each line
            cleaned_line = re.sub(
                r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",
                "",
                line,
            )
            cleaned_lines.append(cleaned_line)

        # Join preserving exact newline structure
        result = "".join(cleaned_lines)

        # Write back
        with open(path, "w", encoding="utf-8") as f:
            f.write(result)

        print(f"✓ Cleaned (newlines preserved): {os.path.basename(path)}")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    files=[]
    for pth in walk_files("."):
        path=Path(pth)
        if path.is_file() and path.suffix=='.log':
            clean_log(path)



if __name__ == "__main__":
    main()

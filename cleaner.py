#!/usr/bin/env python3
"""
Enhanced tmux transcript cleaner - PRESERVES NEWLINES.
Removes ANSI/tmux artifacts while keeping line structure intact.
"""

import os
import sys

import regex as re


def clean_terminal_transcript(path: str) -> None:
    """Clean tmux artifacts while preserving newlines and line structure."""

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
    if len(sys.argv) != 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <transcript_file>")
        sys.exit(1)

    fname = sys.argv[1]
    if not os.path.isfile(fname):
        print(f"Error: '{fname}' not found")
        sys.exit(1)

    clean_terminal_transcript(fname)


if __name__ == "__main__":
    main()

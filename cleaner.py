#!/data/data/com.termux/files/usr/bin/env python3
import os
from pathlib import Path
import sys

from fastwalk import walk_files
import regex as re


def clean_log(path):
    print(f"[] {path}")
    ansi_tmux_re = re.compile(
        rb"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|" rb"\x08|\x0C|\x0F|\x18|\x1C|" rb"\(\d+[a-z]\(B|\(0[Bqtxl]\(B"
    )
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
        content = status_re.sub(b"", content)
        content = ansi_tmux_re.sub(b"", content)
        text = content.decode("utf-8", errors="replace")
        cleaned_lines = []
        for line in text.splitlines(keepends=True):
            cleaned_line = re.sub(
                r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",
                "",
                line,
            )
            cleaned_lines.append(cleaned_line)
        result = "".join(cleaned_lines)
        with open(path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✓ Cleaned (newlines preserved): {os.path.basename(path)}")
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    for pth in walk_files("."):
        path = Path(pth)
        if path.is_file() and path.suffix == ".log":
            clean_log(path)


if __name__ == "__main__":
    main()

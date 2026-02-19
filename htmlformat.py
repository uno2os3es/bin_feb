#!/usr/bin/env python3
from pathlib import Path
import regex as re


HTML_EXTS = {".html", ".htm",".svg",".xml"}
SKIP_TAGS = ("pre", "code")


# Regex to detect opening/closing of skip blocks
SKIP_OPEN_RE = re.compile(r"<\s*(pre|code)\b", re.IGNORECASE)
SKIP_CLOSE_RE = re.compile(r"<\s*/\s*(pre|code)\s*>", re.IGNORECASE)


def split_tags_preserve_indent(line: str) -> str:
    """
    Split multiple tags on same line while preserving original indentation.
    """
    indent = re.match(r"\s*", line).group(0)
    stripped = line.strip()

    # Split between ><
    parts = re.split(r"(>)(\s*)(<)", stripped)

    if len(parts) <= 1:
        return line.rstrip()

    rebuilt = []
    buffer = ""

    i = 0
    while i < len(parts):
        if i + 3 < len(parts) and parts[i + 1] == ">" and parts[i + 3] == "<":
            buffer += parts[i] + ">"
            rebuilt.append(indent + buffer.strip())
            buffer = "<"
            i += 4
        else:
            buffer += parts[i]
            i += 1

    if buffer.strip():
        rebuilt.append(indent + buffer.strip())

    return "\n".join(rebuilt)


def format_file(path: Path):
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    formatted = []
    skip_mode = False

    for line in lines:
        if SKIP_OPEN_RE.search(line):
            skip_mode = True

        if skip_mode:
            formatted.append(line.rstrip())
        else:
            formatted.append(split_tags_preserve_indent(line))

        if SKIP_CLOSE_RE.search(line):
            skip_mode = False

    path.write_text("\n".join(formatted) + "\n", encoding="utf-8")
    print(f"[+] Processed: {path}")


def main():
    for file in Path.cwd().rglob("*"):
        if file.is_file() and file.suffix.lower() in HTML_EXTS:
            format_file(file)


if __name__ == "__main__":
    main()

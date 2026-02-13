#!/usr/bin/env python3
import os
import sys

import regex as re


def read_man_file(filename):
    """Read raw man file content."""
    try:
        with open(
                filename,
                encoding="utf-8",
                errors="ignore",
        ) as f:
            return f.read()
    except FileNotFoundError:
        sys.exit(f"Error: file {filename} not found")


def man_to_markdown(content):
    """
    Convert roff/troff macros to Markdown.
    Handles headings, subsections, bold/italic, paragraphs, lists, code blocks,
    inline code, definitions, examples, and BR/IR macros.
    """
    lines = content.splitlines()
    md_lines = []
    in_code_block = False
    pending_tp = None  # for definition lists (.TP)

    for line in lines:
        # Skip title macros
        if line.startswith(".TH"):
            continue

        # Section headers
        if line.startswith(".SH"):
            header = line[3:].strip()
            md_lines.append(f"# {header.title()}")
            continue

        # Subsection headers
        if line.startswith(".SS"):
            subheader = line[3:].strip()
            md_lines.append(f"## {subheader.title()}")
            continue

        # Bold / Italic
        line = re.sub(r"\.B\s+(.+)", r"**\1**", line)
        line = re.sub(r"\.I\s+(.+)", r"*\1*", line)

        # Bold+Roman (.BR)
        if line.startswith(".BR"):
            parts = line.split(maxsplit=1)
            if len(parts) > 1:
                tokens = parts[1].split('"')
                formatted = []
                for i, t in enumerate(tokens):
                    if not t.strip():
                        continue
                    if i % 2 == 0:  # outside quotes
                        formatted.append(f"**{t.strip()}**")
                    else:  # inside quotes
                        formatted.append(t.strip())
                md_lines.append(" ".join(formatted))
                continue

        # Italic+Roman (.IR)
        if line.startswith(".IR"):
            parts = line.split(maxsplit=1)
            if len(parts) > 1:
                tokens = parts[1].split('"')
                formatted = []
                for i, t in enumerate(tokens):
                    if not t.strip():
                        continue
                    if i % 2 == 0:  # outside quotes
                        formatted.append(f"*{t.strip()}*")
                    else:  # inside quotes
                        formatted.append(t.strip())
                md_lines.append(" ".join(formatted))
                continue

        # Paragraph
        if line.startswith(".PP"):
            md_lines.append("")
            continue

        # Ordered list items (.IP N)
        if line.startswith(".IP"):
            parts = line.split(maxsplit=2)
            if len(parts) >= 2 and parts[1].isdigit():
                num = parts[1]
                item = parts[2] if len(parts) > 2 else ""
                md_lines.append(f"{num}. {item}")
                continue
            if len(parts) >= 2:
                item = parts[1] if len(parts) > 1 else ""
                rest = parts[2] if len(parts) > 2 else ""
                md_lines.append(f"- {item} {rest}".strip())
                continue

        # Definition lists (.TP)
        if line.startswith(".TP"):
            pending_tp = True
            continue
        if pending_tp:
            term = line.strip()
            pending_tp = False
            md_lines.append(f"- {term}:")
            continue

        # Start code block (.nf, .RS, .EX)
        if line.startswith(".nf") or line.startswith(".RS") or line.startswith(
                ".EX"):
            if not in_code_block:
                md_lines.append("```sh")
                in_code_block = True
            continue

        # End code block (.fi, .RE, .EE)
        if line.startswith(".fi") or line.startswith(".RE") or line.startswith(
                ".EE"):
            if in_code_block:
                md_lines.append("```")
                in_code_block = False
            continue

        # Skip other macros
        if line.startswith("."):
            continue

        # Auto-detect shell commands
        if re.match(r"^\s*\$", line) or re.match(
                r"^\s*(ls|cat|grep|echo|pwd|cd|mkdir|rm|touch|man)\b",
                line,
        ):
            if not in_code_block:
                md_lines.append("```sh")
                in_code_block = True
            md_lines.append(line)
            continue
        if in_code_block:
            md_lines.append("```")
            in_code_block = False
        # Inline code formatting for single commands in prose
        line = re.sub(
            r"\b(ls|cat|grep|echo|pwd|cd|mkdir|rm|touch|man)\b",
            r"`\1`",
            line,
        )
        md_lines.append(line)

    # Close any unclosed code block
    if in_code_block:
        md_lines.append("```")

    return "\n".join(md_lines)


def main():
    if len(sys.argv) != 2:
        print("Usage: python man2md.py <manfile>")
        sys.exit(1)

    filename = sys.argv[1]
    raw = read_man_file(filename)
    markdown = man_to_markdown(raw)

    # Save output to .md file
    base, _ = os.path.splitext(filename)
    outname = base + ".md"
    with open(outname, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Converted {filename} → {outname}")


if __name__ == "__main__":
    main()

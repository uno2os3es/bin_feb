#!/usr/bin/env python3
"""
AST-safe PDF Python cleaner with structural corrections:
- Comment narrative text
- Reset indent on def/class
- Force __main__ guard to indent level 1
- AST validate output
"""

import ast
from pathlib import Path

import regex as re

INDENT = " " * 4

DEF_CLASS = re.compile(r"^\s*(def|class)\s+")
MAIN_GUARD = re.compile(r"""^\s*if\s+__name__\s*==\s*['"]__main__['"]\s*:""")

BLOCK_START = re.compile(
    r"""
    ^\s*
    (
        if\s+|
        elif\s+|
        else\s*:|
        for\s+|
        while\s+|
        try\s*:|
        except\s+|
        finally\s*:|
        with\s+
    )
    """,
    re.VERBOSE,
)


def is_code_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    return (s.startswith((
        "def ",
        "class ",
        "if ",
        "elif ",
        "else:",
        "for ",
        "while ",
        "try:",
        "except ",
        "finally:",
        "with ",
        "return",
        "import ",
        "from ",
        "@",
        "#",
    )) or "=" in s or "(" in s or s.endswith(":"))


def clean_text(text: str) -> str:
    out = []
    indent_level = 0
    in_code = False

    for raw in text.splitlines():
        line = raw.rstrip()

        if not line.strip():
            out.append("")
            continue

        # Detect start of code
        if DEF_CLASS.match(line):
            in_code = True

        # Comment narrative text
        if not in_code and not is_code_line(line):
            out.append("# " + line.strip())
            continue

        stripped = line.strip()

        # Rule 1: reset indentation on def/class
        if DEF_CLASS.match(stripped):
            indent_level = 0
            out.append(stripped)
            indent_level = 1
            continue

        # Rule 2: __main__ guard forces indent = 1
        if MAIN_GUARD.match(stripped):
            indent_level = 1
            out.append('if __name__ == "__main__":')
            continue

        # Dedent on exits
        if stripped.startswith(
            ("return", "pass", "break", "continue", "raise")):
            out.append(INDENT * indent_level + stripped)
            indent_level = max(indent_level - 1, 0)
            continue

        # Normal block start
        if BLOCK_START.match(stripped):
            out.append(INDENT * indent_level + stripped)
            indent_level += 1
            continue

        # Normal statement
        out.append(INDENT * indent_level + stripped)

    return "\n".join(out)


def ast_validate(code: str) -> tuple[bool, str | None]:
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"{e.msg} (line {e.lineno}, col {e.offset})"


def main():
    import sys

    src = Path(sys.argv[1])
    dst = Path(sys.argv[1])

    cleaned = clean_text(src.read_text(encoding="utf-8", errors="ignore"))
    ok, err = ast_validate(cleaned)

    if ok:
        dst.write_text(cleaned, encoding="utf-8")
        print(f"✔ AST valid → {dst}")
    else:
        dst.write_text(cleaned, encoding="utf-8")
        #        bad = dst.with_suffix(".invalid.py")
        #       bad.write_text(cleaned, encoding="utf-8")
        print("✘ AST validation failed")
        print(err)
        print("Wrote for inspection")


if __name__ == "__main__":
    main()

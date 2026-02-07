#!/data/data/com.termux/files/usr/bin/env python3
# file: replace_shebang_termux.py

from pathlib import Path

import regex as re

TERMUX_SHEBANG = "#!/data/data/com.termux/files/usr/bin/env python3"
SHEBANG_RE = re.compile(r"^#!.*python[0-9.]*.*$")


def fix_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    if not lines:
        return False

    if SHEBANG_RE.match(lines[0]):
        if lines[0] == TERMUX_SHEBANG:
            return False

        lines[0] = TERMUX_SHEBANG
        path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
        return True

    return False


def main() -> None:
    fixed = 0
    for file in Path(".").rglob("*.py"):
        if fix_file(file):
            fixed += 1
            print(f"Updated: {file}")

    print(f"\nDone. Updated {fixed} files.")


if __name__ == "__main__":
    main()

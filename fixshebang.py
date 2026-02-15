#!/data/data/com.termux/files/usr/bin/env python3

from pathlib import Path

OLD = {
    "#!/data/data/com.termux/files/usr/bin/env python",
    "#!/data/data/com.termux/files/usr/bin/python",
    "#!/data/data/com.termux/files/usr/bin/python3",
    "#!/data/data/com.termux/files/usr/bin/python3.12",
    "#!/usr/bin/env python",
    "#!/usr/bin/env python3",
}
NEW = "#!/data/data/com.termux/files/usr/bin/env python3"


def fix_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    if not lines:
        return False

    if any(lines[0] == p for p in OLD):
            lines[0]=NEW

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

#!/data/data/com.termux/files/usr/bin/env python3
import sys

import regex as re

# Pattern to split on version operators
_VERSION_OP_RE = re.compile(r"\s*(?:===|==|!=|>=|<=|~=|>|<)\s*")


def clean_requirement(line: str) -> str:
    line = line.split("#", 1)[0].strip()
    if not line:
        return ""

    line = line.split(";", 1)[0].strip()
    if not line:
        return ""

    line = re.sub(r"\[.*?\]", "", line).strip()
    if not line:
        return ""

    parts = _VERSION_OP_RE.split(line, maxsplit=1)
    return parts[0].strip()


def group_key(name: str):
    """Group by first character class:
    0 = Uppercase
    1 = Lowercase
    2 = Other
    Sort case-sensitively within group.
    """
    first = name[0]
    if first.isupper():
        return (0, name)
    elif first.islower():
        return (1, name)
    else:
        return (2, name)


def main() -> None:
    if len(sys.argv) != 2:
        print(
            f"Usage: {sys.argv[0]} requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    fname = sys.argv[1]

    try:
        with open(fname, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(
            f"Error: File '{fname}' not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    cleaned = []
    seen = set()
    for line in lines:
        c = clean_requirement(line)
        if c and c not in seen:
            cleaned.append(c)
            seen.add(c)

    cleaned = sorted(cleaned, key=group_key)

    with open(fname, "w", encoding="utf-8") as f:
        for item in cleaned:
            f.write(item + "\n")

    print("\n=== Cleaned Requirements ===")
    for item in cleaned:
        print(item)


if __name__ == "__main__":
    main()

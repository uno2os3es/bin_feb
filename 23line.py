#!/data/data/com.termux/files/usr/bin/env python3
"""Extract first 13 lines of all .py files recursively.
Store all results in a list, deduplicate them,
then write ONLY unique entries to all.txt
with 3 blank lines between them.
"""

import os

import dh

EXT = [
    ".py",
    ".h",
    ".c",
    ".cpp",
    ".cc",
    ".cxx",
    ".hh",
    ".hpp",
    ".h",
    ".hxx",
]


def get_first_13(path: str) -> str:
    """Why: Ensures safe read even for short files."""
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    return "".join(lines[:13])


def main() -> None:
    output_path = "all.txt"
    collected = []

    for base, _, files in os.walk(os.getcwd()):
        for name in files:
            ext = dh.get_ext(name)
            if ext not in EXT:
                continue

            path = os.path.join(base, name)

            # Prevent including output file itself
            if os.path.abspath(path) == os.path.abspath(output_path):
                continue

            snippet = get_first_13(path)

            # Store only the snippet (no header)
            collected.append(snippet)

    # Deduplicate while preserving content
    unique_collected = list(set(collected))

    with open(output_path, "w", encoding="utf-8") as out:
        for snippet in unique_collected:
            out.write(snippet)
            out.write("\n\n\n")  # 3 blank lines

    print(f"Unique snippets saved → {output_path}")
    print(f"Total unique blocks: {len(unique_collected)}")


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/python
import argparse
import os

import regex as re


def replace_in_files(search_text, replace_text, dry_run=False):
    exclude_dirs = {".git", "build", "dist"}
    # Use word boundaries \b to ensure 're' doesn't match 'requests'
    pattern = re.compile(r"\b" + re.escape(search_text) + r"\b")

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for filename in files:
            file_path = os.path.join(root, filename)

            try:
                with open(
                        file_path,
                        encoding="utf-8",
                ) as f:
                    lines = f.readlines()

                new_lines = []
                changed = False

                for i, line in enumerate(lines):
                    if pattern.search(line):
                        new_line = pattern.sub(replace_text, line)
                        if dry_run:
                            print(
                                f"[DRY RUN] Match found in {file_path} on line {i + 1}:"
                            )
                            print(f"  - Old: {line.strip()}")
                            print(f"  + New: {new_line.strip()}")
                        new_lines.append(new_line)
                        changed = True
                    else:
                        new_lines.append(line)

                if changed and not dry_run:
                    with open(
                            file_path,
                            "w",
                            encoding="utf-8",
                    ) as f:
                        f.writelines(new_lines)
                    print(f"Updated: {file_path}")

            except (
                    UnicodeDecodeError,
                    PermissionError,
            ):
                continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recursively replace text in files.")
    parser.add_argument("search", help="The text to search for")
    parser.add_argument("replace", help="The replacement text")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying them",
    )

    args = parser.parse_args()

    if args.dry_run:
        print("--- RUNNING IN DRY RUN MODE (No files will be modified) ---")

    replace_in_files(
        args.search,
        args.replace,
        dry_run=args.dry_run,
    )

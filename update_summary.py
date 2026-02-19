#!/data/data/com.termux/files/usr/bin/env python3
# update_summary.py - Auto-updates SUMMARY.md with all .md files in the directory

import os
import regex as re


def update_summary():
    # Get all .md files in the current directory, excluding SUMMARY.md
    md_files = [f for f in os.listdir(".") if f.endswith(".md") and f != "SUMMARY.md"]
    md_files.sort()  # Sort alphabetically

    # Read the existing SUMMARY.md header
    with open("SUMMARY.md", "r") as f:
        lines = f.readlines()
    header = []
    for line in lines:
        if line.strip() and not line.strip().startswith("- ["):
            header.append(line)
        else:
            break

    # Generate new chapter entries
    new_entries = []
    for md_file in md_files:
        # Use the filename (without .md) as the chapter title
        title = os.path.splitext(md_file)[0].replace("_", " ").title()
        entry = f"- [{title}](.{os.sep}{md_file})\n"
        new_entries.append(entry)

    # Write the updated SUMMARY.md
    with open("SUMMARY.md", "w") as f:
        f.writelines(header)
        f.write("\n")  # Add a blank line after the header
        f.writelines(new_entries)

    print(f"Updated SUMMARY.md with {len(new_entries)} chapters.")


if __name__ == "__main__":
    update_summary()

#!/data/data/com.termux/files/usr/bin/env python3
import os


def update_summary():
    md_files = [f for f in os.listdir(".") if f.endswith(".md") and f != "SUMMARY.md"]
    md_files.sort()
    with open("SUMMARY.md") as f:
        lines = f.readlines()
    header = []
    for line in lines:
        if line.strip() and not line.strip().startswith("- ["):
            header.append(line)
        else:
            break
    new_entries = []
    for md_file in md_files:
        title = os.path.splitext(md_file)[0].replace("_", " ").title()
        entry = f"- [{title}](.{os.sep}{md_file})\n"
        new_entries.append(entry)
    with open("SUMMARY.md", "w") as f:
        f.writelines(header)
        f.write("\n")
        f.writelines(new_entries)
    print(f"Updated SUMMARY.md with {len(new_entries)} chapters.")


if __name__ == "__main__":
    update_summary()

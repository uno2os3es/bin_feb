#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path


def main() -> None:
    hist_file = Path.home() / ".bash_history"
    if not hist_file.exists():
        print("~/.bash_history does not exist.")
        return
    with hist_file.open("r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    seen = set()
    unique_lines = []
    histlen = len(lines)
    print(f"history length: {histlen}")
    for line in lines:
        stripped = line.rstrip("\n")
        if stripped not in seen:
            seen.add(stripped)
            unique_lines.append(stripped)
    with hist_file.open("w", encoding="utf-8") as f:
        for line in unique_lines:
            f.write(line + "\n")


if __name__ == "__main__":
    main()

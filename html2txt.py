#!/data/data/com.termux/files/usr/bin/env python3
import os
import sys


def strip_html_tags(input_file, output_file) -> None:
    inside_tag = False

    with (
            open(
                input_file,
                encoding="utf-8",
                errors="ignore",
            ) as f,
            open(output_file, "w", encoding="utf-8") as out,
    ):
        for line in f:
            buf = []
            for ch in line:
                if ch == "<":
                    inside_tag = True
                    continue
                if ch == ">":
                    inside_tag = False
                    continue
                if not inside_tag:
                    buf.append(ch)

            cleaned = "".join(buf).strip()
            if cleaned:
                out.write(cleaned + "\n")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: html2txt.py <input.html>")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.isfile(input_file):
        print("Error: file not found:", input_file)
        sys.exit(1)

    base, _ = os.path.splitext(input_file)
    output_file = base + ".txt"

    strip_html_tags(input_file, output_file)
    print("Saved:", output_file)


if __name__ == "__main__":
    main()

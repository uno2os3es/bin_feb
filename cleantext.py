#!/data/data/com.termux/files/usr/bin/env python3
import sys
import unicodedata


def clean_file(filename):
    try:
        # Read the original file
        with open(filename, encoding="utf-8") as f:
            lines = f.readlines()

        cleaned_lines = []
        for line in lines:
            # unicodedata.category(c) 'C' stands for 'Other' (Control, Private Use, etc.)
            # This removes non-printing characters but keeps standard spaces and newlines
            cleaned_line = "".join(ch for ch in line if unicodedata.category(ch)[0] != "C" or ch in "\n\r\t")
            cleaned_lines.append(cleaned_line)

        # Overwrite the file with the cleaned version
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)

        print(f"Successfully cleaned: {filename}")

    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_text.py <filename>")
    else:
        target_file = sys.argv[1]
        clean_file(target_file)

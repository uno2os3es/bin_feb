#!/data/data/com.termux/files/usr/bin/env python3
import os

import regex as re

# Define file extensions for different programming languages
LANG_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js"],
    "java": [".java"],
    "c": [".c"],
    "cpp": [".cpp", ".h"],
    "html": [".html"],
    "css": [".css"],
    "ruby": [".rb"],
    "php": [".php"],
}

# Regular expressions for detecting comments (basic ones)
COMMENT_PATTERNS = {
    "python": r"^\s*#",  # Python comments
    "javascript": r"^\s*//",  # JavaScript single-line comments
    "java": r"^\s*//",  # Java single-line comments
    "c": r"^\s*//",  # C single-line comments
    "cpp": r"^\s*//",  # C++ single-line comments
    "html": r"^\s*<!--",  # HTML comments
    "css": r"^\s*/\*",  # CSS comments
    "ruby": r"^\s*#",  # Ruby comments
    "php": r"^\s*//",  # PHP single-line comments
}

# Shebang-to-language mapping for files without extensions
SHEBANG_LANGUAGES = {
    "python": [
        "#!/usr/bin/python",
        "#!/usr/bin/python3",
        "#!/bin/python3",
    ],
    "bash": ["#!/bin/bash"],
    "ruby": ["#!/usr/bin/ruby", "#!/bin/ruby"],
    "perl": ["#!/usr/bin/perl"],
    "node": ["#!/usr/bin/node", "#!/bin/node"],
    "sh": ["#!/bin/sh"],  # for shell scripts (e.g., Bash, SH)
}


def get_language_from_shebang(file_path):
    """Try to detect the language of a file from its shebang (if no extension is present)."""
    if ".git" in str(file_path):
        return None
    try:
        with open(file_path, encoding="utf-8") as file:
            first_line = file.readline().strip()
            for (
                lang,
                shebangs,
            ) in SHEBANG_LANGUAGES.items():
                for shebang in shebangs:
                    if first_line.startswith(shebang):
                        return lang
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return None  # If no shebang matches, return None


def count_lines_of_code(file_path, lang):
    """Count the lines of code, comments, and blank lines in a given file."""
    if ".git" in str(file_path):
        return 0, 0, 0
    with open(file_path, encoding="utf-8") as file:
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        for line in file:
            if not line.strip():  # Blank line
                blank_lines += 1
            elif re.match(
                COMMENT_PATTERNS.get(lang, ""),
                line,
            ):  # Comment line
                comment_lines += 1
            else:  # Code line
                code_lines += 1
    return code_lines, comment_lines, blank_lines


def scan_directory(directory="."):
    """Scan the directory for source code files and count lines."""
    stats = {
        "total": {
            "code": 0,
            "comments": 0,
            "blank": 0,
        },
        "languages": {
            lang: {
                "code": 0,
                "comments": 0,
                "blank": 0,
            }
            for lang in LANG_EXTENSIONS
        },
    }

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[1].lower()

            # Check for files without extensions
            if not file_extension:  # No extension, check shebang
                lang = get_language_from_shebang(file_path)
                if lang:
                    # Count lines for files with no extension based on shebang
                    code, comments, blanks = count_lines_of_code(file_path, lang)
                    stats["languages"][lang]["code"] += code
                    stats["languages"][lang]["comments"] += comments
                    stats["languages"][lang]["blank"] += blanks
                    stats["total"]["code"] += code
                    stats["total"]["comments"] += comments
                    stats["total"]["blank"] += blanks
                    continue  # Skip extension-based checks for these files

            # Check for extension-based language detection
            for (
                lang,
                extensions,
            ) in LANG_EXTENSIONS.items():
                if file_extension in extensions:
                    code, comments, blanks = count_lines_of_code(file_path, lang)
                    stats["languages"][lang]["code"] += code
                    stats["languages"][lang]["comments"] += comments
                    stats["languages"][lang]["blank"] += blanks
                    stats["total"]["code"] += code
                    stats["total"]["comments"] += comments
                    stats["total"]["blank"] += blanks
                    break  # No need to check other languages once matched

    return stats


def display_stats(stats) -> None:
    """Display the line count statistics."""
    # Display total stats
    print(f"Total lines of code: {stats['total']['code']}")
    print(f"Total comment lines: {stats['total']['comments']}")
    print(f"Total blank lines: {stats['total']['blank']}\n")

    # Display stats by language (only if code lines are > 0)
    print("Language-based statistics:")
    for lang, lang_stats in stats["languages"].items():
        if lang_stats["code"] > 0:  # Only show the language if code lines > 0
            print(f"\n{lang.capitalize()}:")
            print(f"  Code lines: {lang_stats['code']}")
            print(f"  Comment lines: {lang_stats['comments']}")
            print(f"  Blank lines: {lang_stats['blank']}")


if __name__ == "__main__":
    # Start scanning the current directory (.)
    stats = scan_directory()
    display_stats(stats)

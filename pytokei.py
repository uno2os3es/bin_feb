#!/data/data/com.termux/files/usr/bin/env python3
import os

import regex as re

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

COMMENT_PATTERNS = {
    "python": r"^\s*#",
    "javascript": r"^\s*//",
    "java": r"^\s*//",
    "c": r"^\s*//",
    "cpp": r"^\s*//",
    "html": r"^\s*<!--",
    "css": r"^\s*/\*",
    "ruby": r"^\s*#",
    "php": r"^\s*//",
}

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
    "sh": ["#!/bin/sh"],
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
    return None


def count_lines_of_code(file_path, lang):
    """Count the lines of code, comments, and blank lines in a given file."""
    if ".git" in str(file_path):
        return 0, 0, 0
    with open(file_path, encoding="utf-8") as file:
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        for line in file:
            if not line.strip():
                blank_lines += 1
            elif re.match(
                COMMENT_PATTERNS.get(lang, ""),
                line,
            ):
                comment_lines += 1
            else:
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

            if not file_extension:
                lang = get_language_from_shebang(file_path)
                if lang:
                    code, comments, blanks = count_lines_of_code(file_path, lang)
                    stats["languages"][lang]["code"] += code
                    stats["languages"][lang]["comments"] += comments
                    stats["languages"][lang]["blank"] += blanks
                    stats["total"]["code"] += code
                    stats["total"]["comments"] += comments
                    stats["total"]["blank"] += blanks
                    continue

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
                    break

    return stats


def display_stats(stats) -> None:
    """Display the line count statistics."""
    print(f"Total lines of code: {stats['total']['code']}")
    print(f"Total comment lines: {stats['total']['comments']}")
    print(f"Total blank lines: {stats['total']['blank']}\n")

    print("Language-based statistics:")
    for lang, lang_stats in stats["languages"].items():
        if lang_stats["code"] > 0:
            print(f"\n{lang.capitalize()}:")
            print(f"  Code lines: {lang_stats['code']}")
            print(f"  Comment lines: {lang_stats['comments']}")
            print(f"  Blank lines: {lang_stats['blank']}")


if __name__ == "__main__":
    stats = scan_directory()
    display_stats(stats)

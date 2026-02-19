#!/data/data/com.termux/files/usr/bin/env python3
import os


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
                    code, comments, blanks = count_lines_of_code(
                        file_path,
                        lang,
                    )
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
                    code, comments, blanks = count_lines_of_code(
                        file_path,
                        lang,
                    )
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

    for lang_stats in stats["languages"].values():
        if lang_stats["code"] > 0:
            pass


if __name__ == "__main__":
    stats = scan_directory()
    display_stats(stats)

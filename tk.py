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

            # Check for files without extensions
            if not file_extension:  # No extension, check shebang
                lang = get_language_from_shebang(file_path)
                if lang:
                    # Count lines for files with no extension based on shebang
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
                    continue  # Skip extension-based checks for these files

            # Check for extension-based language detection
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
                    break  # No need to check other languages once matched

    return stats


def display_stats(stats) -> None:
    """Display the line count statistics."""
    # Display total stats

    # Display stats by language (only if code lines are > 0)
    for lang_stats in stats["languages"].values():
        if lang_stats["code"] > 0:  # Only show the language if code lines > 0
            pass


if __name__ == "__main__":
    # Start scanning the current directory (.)
    stats = scan_directory()
    display_stats(stats)

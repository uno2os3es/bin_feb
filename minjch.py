#!/data/data/com.termux/files/usr/bin/env python3
"""Recursively minify JS, CSS, JSON, and HTML files in the current directory.
OVERWRITES originals.
Uses multiprocessing for speed.
"""

import json
import multiprocessing
import os

from rcssmin import cssmin
import regex as re
from rjsmin import jsmin


def minify_html(html: str) -> str:
    """Why: Simple compacting without breaking structure."""
    html = re.sub(r">\s+<", "><", html)  # collapse >   < gaps
    html = re.sub(r"\s{2,}", " ", html)  # collapse spaces
    return html.strip()


def process_file(path: str) -> str:
    """Worker for multiprocessing."""
    try:
        ext = os.path.splitext(path)[1].lower()

        with open(path, encoding="utf-8") as f:
            content = f.read()

        if ext == ".js":
            content = jsmin(content)

        elif ext == ".css":
            content = cssmin(content)

        elif ext == ".json":
            parsed = json.loads(content)
            content = json.dumps(parsed, separators=(",", ":"))

        elif ext in {".html", ".htm"}:
            content = minify_html(content)

        else:
            return f"SKIP → {path}"

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"OK → {path}"

    except Exception as e:
        return f"ERR ({path}): {e}"


def collect_files() -> list:
    """Find all supported file types."""
    supported = (
        ".js",
        ".css",
        ".json",
        ".html",
        ".htm",
    )
    excluded_min = (".min.js", ".min.css")
    out = []

    for base, _, files in os.walk(os.getcwd()):
        for name in files:
            path = os.path.join(base, name)
            lower = name.lower()

            if lower.endswith(excluded_min):
                continue

            if lower.endswith(supported):
                out.append(path)

    return out


def main() -> None:
    files = collect_files()

    if not files:
        print("No supported files found.")
        return

    print(f"Found {len(files)} files. Starting multiprocessing...")

    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        for result in pool.imap_unordered(process_file, files):
            print(result)


if __name__ == "__main__":
    main()

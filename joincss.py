#!/usr/bin/env python3

import contextlib
import os
import re
import sys
import tempfile
from pathlib import Path

LOCAL_FONT_BASE = Path("/sdcard/_static/fonts")
FONT_EXTS = {".woff", ".woff2", ".ttf", ".otf", ".eot"}
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
IMPORT_RE = re.compile(r"@import\s+url\([^)]+fonts\.googleapis[^)]+\);?", re.I)
FAMILY_RULES = {
    "roboto": "roboto",
    "lato": "lato",
    "opensans": "opensans",
    "open-sans": "opensans",
    "fontawesome": "fa",
    "fa-": "fa",
}

URL_RE = re.compile(
    r'url\((["\']?)(https?://[^)]+?\.(?:woff2?|ttf|otf|eot))\1\)',
    re.I,
)


def find_css(paths):
    seen = set()
    result = []

    for p in paths:
        p = Path(p)

        if p.is_file() and p.suffix.lower() == ".css":
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                result.append(rp)

        elif p.is_dir():
            pattern = "**/*.css"
            for f in sorted(p.glob(pattern)):
                rp = f.resolve()
                if rp not in seen:
                    seen.add(rp)
                    result.append(rp)

        else:
            print(f"Skipping invalid path: {p}", file=sys.stderr)

    return result


def read_css(files):
    charset_line = None
    chunks = []

    def localize_font_url(match):
        url = match.group(2)
        filename = url.split("/")[-1]
        return f'url("{LOCAL_FONT_BASE}/{filename}")'

    for file in files:
        text = file.read_text(errors="ignore")
        text = IMPORT_RE.sub("", text)
        text = URL_RE.sub(localize_font_url, text)
        lines = text.splitlines()
        cleaned = []

        for line in lines:
            stripped = line.strip().lower()

            # capture first @charset only
            if stripped.startswith("@charset"):
                if charset_line is None:
                    charset_line = line.strip()
                continue

            cleaned.append(line)

        chunks.append((file, "\n".join(cleaned).strip()))

    return charset_line, chunks


def atomic_write(path, content):
    path = Path(path)
    tmp = tempfile.NamedTemporaryFile(delete=False, dir=str(path.parent), mode="w", encoding="utf-8")
    try:
        tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        os.replace(tmp.name, path)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp.name)


def join_css(files, output):
    charset, chunks = read_css(files)

    parts = []

    if charset:
        parts.append(charset + "\n")

    for file, content in chunks:
        parts.append(f"\n/* ===== {file.name} ===== */\n{content}\n")

    final_css = "\n".join(parts).strip() + "\n"
    atomic_write(output, final_css)


def main():
    files = find_css(".")
    if not files:
        print("No CSS files found.", file=sys.stderr)
        sys.exit(1)

    join_css(files, "merged.css")
    print(f"Joined {len(files)} files -> merged.css")


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/env python3
import os
import sys

import regex as re
from fontTools.ttLib import TTFont
from termcolor import cprint

# ---------- helpers ----------


def is_ascii_printable(s: str) -> bool:
    return all(32 <= ord(c) <= 126 for c in s)


def clean_filename(s: str) -> str:
    s = re.sub(r"[^\w\-\.]", "", s)
    return s.strip("_-.")


def unique_path(path: str) -> str:
    base, ext = os.path.splitext(path)
    i = 2
    new = path
    while os.path.exists(new):
        new = f"{base}_{i}{ext}"
        i += 1
    return new


def get_best_name(font, name_id):
    fallback = None

    for rec in font["name"].names:
        if rec.nameID != name_id:
            continue

        try:
            name = rec.toUnicode().strip()
        except Exception:
            continue

        if rec.platformID == 3 and rec.langID == 0x0409:
            return name

        if is_ascii_printable(name):
            fallback = name

    return fallback


def get_font_names(path):
    font = TTFont(path)

    family = get_best_name(font, 1)
    subfamily = get_best_name(font, 2)

    if not family:
        return None, None

    family = clean_filename(family)

    subfamily = "Regular" if not subfamily else clean_filename(subfamily)

    if subfamily.lower() == family.lower():
        subfamily = "Regular"

    return family, subfamily


def main():
    if len(sys.argv) < 2:
        print("usage: font_rename.py <fontfile>")
        return 1

    fn = sys.argv[1]

    try:
        family, style = get_font_names(fn)
    except Exception as e:
        cprint(f"error: {e}", "magenta")
        return 1

    if not family:
        cprint("name not found", "magenta")
        return 1

    ext = os.path.splitext(fn)[1].lower()
    new_name = f"{family}-{style}{ext}"
    new_name = unique_path(new_name)

    if os.path.abspath(fn) == os.path.abspath(new_name):
        cprint("no change", "blue")
        return 0

    os.rename(fn, new_name)
    cprint(f"{fn} -> {new_name}", "green")
    return 0


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
css_bundle.py — merge CSS, deduplicate rules, and bundle assets.

Features
--------
• Merge CSS files in given order
• Remove Google Fonts imports
• Rewrite font URLs to local fonts folder
• Deduplicate CSS rules (last definition wins)
• Bundle assets (fonts/images) into output directory
• Rewrite URLs to bundled assets

Usage
-----
python css_bundle.py *.css -o bundle.css --assets-dir ./assets

Result:
  bundle.css
  assets/
      fonts...
      images...
"""

import argparse
import re
import shutil
from pathlib import Path

LOCAL_FONT_BASE = Path("/sdcard/_static/fonts")

IMPORT_RE = re.compile(r"@import\s+url\([^)]+fonts\.googleapis[^)]+\);?", re.I)

URL_RE = re.compile(r'url\((["\']?)([^)]+)\1\)', re.I)

RULE_RE = re.compile(r"([^{]+)\{([^}]*)\}", re.S)

FONT_EXTS = {".woff", ".woff2", ".ttf", ".otf", ".eot"}
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}


def detect_family(filename: str):
    n = filename.lower()
    if "roboto" in n:
        return "roboto"
    if "lato" in n:
        return "lato"
    if "opensans" in n or "open-sans" in n:
        return "opensans"
    if "fa" in n or "fontawesome" in n:
        return "fa"
    return None


def copy_asset(src, assets_dir):
    src = Path(src)
    if not src.exists():
        return None

    ext = src.suffix.lower()

    if ext in FONT_EXTS:
        fam = detect_family(src.name)
        dest_dir = assets_dir / "fonts" / (fam or "")
    else:
        dest_dir = assets_dir / "images"

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name

    if not dest.exists():
        shutil.copy2(src, dest)

    return dest


def rewrite_urls(css_text, css_dir, assets_dir):
    def repl(match):
        url = match.group(2).strip().strip("\"'")
        if url.startswith("http"):
            filename = url.split("/")[-1]
            fam = detect_family(filename)
            if fam:
                LOCAL_FONT_BASE / fam / filename
                return f'url("assets/fonts/{fam}/{filename}")'
            return match.group(0)

        asset_path = (css_dir / url).resolve()
        copied = copy_asset(asset_path, assets_dir)
        if copied:
            rel = copied.relative_to(assets_dir.parent)
            return f'url("{rel}")'

        return match.group(0)

    return URL_RE.sub(repl, css_text)


def deduplicate_rules(css_text):
    rules = {}
    order = []

    for sel, body in RULE_RE.findall(css_text):
        key = sel.strip()
        if key not in rules:
            order.append(key)
        rules[key] = body.strip()

    merged = []
    for sel in order:
        merged.append(f"{sel} {{\n{rules[sel]}\n}}")

    return "\n\n".join(merged)


def process_css(file, assets_dir):
    text = file.read_text(errors="ignore")
    text = IMPORT_RE.sub("", text)
    return rewrite_urls(text, file.parent, assets_dir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    #    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--output", default="bundle.css")
    ap.add_argument("--assets-dir", default="/sdcard/_static/assets")

    args = ap.parse_args()

    assets_dir = Path(args.assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    files = args.files or [str(p) for p in Path(".").glob("*.css")]
    chunks = []

    for f in files:
        p = Path(f)
        if p.exists() and p.suffix.lower() == ".css":
            chunks.append(process_css(p, assets_dir))

    merged = "\n\n".join(chunks)
    merged = deduplicate_rules(merged)

    Path(args.output).write_text(merged)
    print("Bundle complete.")
    print("CSS:", args.output)
    print("Assets:", assets_dir)


if __name__ == "__main__":
    main()

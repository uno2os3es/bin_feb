#!/usr/bin/env python3

import regex as re
from pathlib import Path

REMOTE_PREFIXES = ("http://", "https://", "//")


# ---------- HTML Processing ----------

IMG_TAG_RE = re.compile(r'<img\b[^>]*\bsrc\s*=\s*["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)


def remove_remote_html_images(text: str) -> str:
    def repl(match):
        src = match.group(1)
        if src.startswith(REMOTE_PREFIXES):
            return ""
        return match.group(0)

    return IMG_TAG_RE.sub(repl, text)


MD_INLINE_IMG_RE = re.compile(r"!\[.*?\]\((.*?)\)", re.IGNORECASE)

MD_REF_IMG_RE = re.compile(r"!\[.*?\]\[(.*?)\]", re.IGNORECASE)

MD_REF_DEF_RE = re.compile(r"^\s*\[(.*?)\]:\s*(\S+)", re.MULTILINE)


def remove_remote_md_images(text: str) -> str:
    def inline_repl(match):
        url = match.group(1)
        if url.startswith(REMOTE_PREFIXES):
            return ""
        return match.group(0)

    text = MD_INLINE_IMG_RE.sub(inline_repl, text)

    remote_ids = set()
    for m in MD_REF_DEF_RE.finditer(text):
        ref_id, url = m.groups()
        if url.startswith(REMOTE_PREFIXES):
            remote_ids.add(ref_id)

    def ref_repl(match):
        ref_id = match.group(1)
        if ref_id in remote_ids:
            return ""
        return match.group(0)

    text = MD_REF_IMG_RE.sub(ref_repl, text)

    def def_repl(match):
        ref_id, url = match.groups()
        if ref_id in remote_ids:
            return ""
        return match.group(0)

    text = MD_REF_DEF_RE.sub(def_repl, text)

    return text


def process_file(path: Path):
    original = path.read_text(encoding="utf-8", errors="ignore")

    if path.suffix.lower() in (".html", ".htm"):
        modified = remove_remote_html_images(original)
    elif path.suffix.lower() in {".md", ".txt"}:
        modified = remove_remote_md_images(original)
    else:
        return

    if modified != original:
        path.write_text(modified, encoding="utf-8")
        print(f"Modified: {path}")


def main():
    for file in Path(".").rglob("*"):
        if file.is_file() and file.suffix.lower() in (".html", ".htm", ".md"):
            process_file(file)


if __name__ == "__main__":
    main()

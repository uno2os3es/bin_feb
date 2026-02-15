#!/usr/bin/env python3
import os
import unicodedata
from html.parser import HTMLParser
from pathlib import Path


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title and self.title is None:
            self.title = data.strip()


def extract_title(html_path: Path) -> str | None:
    try:
        parser = TitleParser()
        parser.feed(html_path.read_text(errors="ignore"))
        return parser.title
    except Exception:
        return None


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    temp = text
    text = text.lower()
    text = text.strip("?")
    text = text.replace("=", "").replace(" ", "_")
    text = text.replace(";", "")
    if len(text) < 2:
        return temp.strip(":").strip("?").strip("=")
    return text.strip(":")


def unique_path(path: Path) -> Path:
    counter = 1
    new_path = path
    while new_path.exists():
        new_path = path.with_stem(f"{path.stem}-{counter}")
        counter += 1
    return new_path


def rename_html_files(root: Path):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if not name.lower().endswith((".html", ".htm")):
                continue

            old_path = Path(dirpath) / name
            title = extract_title(old_path)

            if not title:
                continue

            slug = slugify(title)
            if not slug:
                continue

            new_path = old_path.with_name(slug + old_path.suffix)
            new_path = unique_path(new_path)

            if old_path == new_path:
                continue

            print(f"{old_path} -> {new_path}")
            old_path.rename(new_path)


if __name__ == "__main__":
    dir = Path().cwd()
    rename_html_files(dir)

#!/data/data/com.termux/files/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

import regex as re
from dh import MIME_TO_EXT, TXT_EXT

if TYPE_CHECKING:
    from collections.abc import Iterable

OUTPUT_DIR = Path("extracted_base64")
HTML_EXTENSIONS = TXT_EXT
DATA_URL_RE = re.compile(
    r"^data:(?:application/(?:font\-woff;charset=utf\-8|(?:vnd\.ms\-fontobject|octet\-stream));base64,|(?:(?:image/svg\+xml|font/(?:woff2|ttf))|font/woff);base64,)$",
    re.IGNORECASE,
)

# DATA_URL_RE = re.compile("data:(?P<mime>[-\w.+/]+);base64,(?P<data>[A-Za-z0-9+/=\s]+)",re.IGNORECASE,)
MIME_EXTENSION_MAP = MIME_TO_EXT


def iter_html_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.suffix.lower() in HTML_EXTENSIONS and path.is_file():
            yield path


def infer_extension(mime: str) -> str:
    return MIME_EXTENSION_MAP.get(
        mime.lower(),
        mime.rsplit("/", maxsplit=1)[-1],
    )


def decode_base64(data: str) -> bytes:
    cleaned = "".join(data.split())
    return base64.b64decode(cleaned, validate=False)


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_from_html(
    html: str,
) -> Iterable[tuple[str, bytes]]:
    for match in DATA_URL_RE.finditer(html):
        mime = match.group("mime")
        raw_data = match.group("data")
        try:
            decoded = decode_base64(raw_data)
        except Exception:
            continue
        yield mime, decoded


def save_asset(mime: str, data: bytes) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ext = infer_extension(mime)
    digest = content_hash(data)
    filename = f"{digest}.{ext}"
    path = OUTPUT_DIR / filename
    if not path.exists():
        path.write_bytes(data)
    return path


def main() -> None:
    root = Path.cwd()
    seen_hashes = set()
    extracted_count = 0
    for html_file in iter_html_files(root):
        try:
            html = html_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for mime, data in extract_from_html(html):
            digest = content_hash(data)
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            save_asset(mime, data)
            extracted_count += 1


if __name__ == "__main__":
    main()

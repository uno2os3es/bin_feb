#!/data/data/com.termux/files/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

import regex as re

if TYPE_CHECKING:
    from collections.abc import Iterable

OUTPUT_DIR = Path("extracted_base64")
HTML_EXTENSIONS = {
    ".elv",
    ".gep",
    ".hip",
    ".html_t",
    ".js_t",
    ".css_t",
    ".me",
    ".nu",
    ".ctypes",
    ".rlib",
    ".ansitxt",
    ".api",
    ".awk",
    ".asdl",
    ".alias",
    ".applescript",
    ".asm",
    ".s",
    ".bnf",
    ".bashrc",
    ".bash",
    ".bat",
    ".csh",
    ".c-diff",
    ".c",
    ".cs",
    ".hh",
    ".hpp",
    ".hxx",
    ".cc",
    ".cpp",
    ".cxx",
    ".hpp11",
    ".h",
    ".cgi",
    ".cuh",
    ".cu",
    ".css",
    ".charsets",
    ".cheat",
    ".modulemap",
    ".coffee",
    ".csv",
    ".cjs",
    ".cfg",
    ".conf",
    ".conffiles",
    ".pxd",
    ".pxi",
    ".pyx",
    ".d",
    ".control",
    ".postinst",
    ".postrm",
    ".def",
    ".deps",
    ".desktop",
    ".dict",
    ".dockerfile",
    ".el",
    ".ent",
    ".env",
    ".faq",
    ".feature-removal-schedule",
    ".fish",
    ".flow",
    ".glsl",
    ".gpl",
    ".info",
    ".info-1",
    ".info-2",
    ".info-3",
    ".gresource",
    ".gyp",
    ".gypi",
    ".pot",
    ".githook",
    ".glade",
    ".go",
    ".hhc",
    ".hhp",
    ".htm",
    ".html",
    ".hbs",
    ".hint",
    ".ini",
    ".ispc",
    ".inc",
    ".install",
    ".jsonl",
    ".json-tmlanguage",
    ".jwt",
    ".json",
    ".properties",
    ".java",
    ".js",
    ".jst",
    ".jinja",
    ".jinja2",
    ".ipynb",
    ".kv",
    ".keymap",
    ".ll",
    ".sty",
    ".lark",
    ".l",
    ".la",
    ".lst",
    ".log",
    ".m4",
    ".m4f",
    ".mhtml",
    ".make",
    ".markdown",
    ".md",
    ".markdown-it",
    ".menu",
    ".metainfo",
    ".mod",
    ".nanorc",
    ".ninja",
    ".nix",
    ".mli",
    ".ml",
    ".m",
    ".mm",
    ".odt",
    ".opts",
    ".org",
    ".pas",
    ".patch",
    ".patches",
    ".pm",
    ".pl",
    ".pod",
    ".txt",
    ".policy",
    ".ps1",
    ".prop",
    ".props",
    ".plist",
    ".proto",
    ".pygments",
    ".pyw",
    ".pth",
    ".py",
    ".pyi",
    ".qml",
    ".qmltypes",
    ".qhcp",
    ".qhp",
    ".qph",
    ".qrc",
    ".qdocconf",
    ".qdoc",
    ".qdocinc",
    ".qm",
    ".rnc",
    ".rng",
    ".spec",
    ".rc",
    ".rb",
    ".rs",
    ".scss",
    ".sha256sum",
    ".sip",
    ".sip5",
    ".sql",
    ".swg",
    ".svg",
    ".scm",
    ".settings",
    ".sh",
    ".shell",
    ".stderr",
    ".srt",
    ".swift",
    ".syntax",
    ".service",
    ".tcsh",
    ".toml",
    ".tag",
    ".tcl",
    ".tex",
    ".template",
    ".tmpl",
    ".tpl",
    ".tap",
    ".tmlanguage",
    ".theme",
    ".thrift",
    ".tsx",
    ".ts",
    ".vapi",
    ".version",
    ".vim",
    ".vsmacros",
    ".xbm",
    ".its",
    ".xsd",
    ".xml",
    ".xsl",
    ".xslt",
    ".xcscheme",
    ".xcsettings",
    ".yaml",
    ".yml",
    ".yapf",
    ".y",
    ".yy",
    ".zsh",
    ".pc",
    ".rst",
    ".vcf",
    ".wasm",
}
DATA_URL_RE = re.compile(
    r"data:(?P<mime>[-\w.+/]+);base64,(?P<data>[A-Za-z0-9+/=\s]+)",
    re.IGNORECASE,
)
MIME_EXTENSION_MAP: dict[str, str] = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/gif": "gif",
    "image/heif": "heif",
    "image/webp": "webp",
    "image/svg+xml": "svg",
    "application/pdf": "pdf",
    "application/octet-stream": "bin",
    "font/woff": "woff",
    "font/woff2": "woff2",
    "application/font-woff": "woff",
    "application/font-woff2": "woff2",
    "font/ttf": "ttf",
    "font/otf": "otf",
    "font/eot": "eot",
    "font/svg": "svg",
    "application/javascript": "js",
}


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

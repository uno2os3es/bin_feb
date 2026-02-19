#!/data/data/com.termux/files/usr/bin/env python3
import os

import magic

MIME_TO_EXT = {
    "text/html": "html",
    "application/json": "json",
    "application/javascript": "js",
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
    "application/zip": "zip",
    "application/gzip": "gz",
    "application/x-tar": "tar",
    "text/xml": "xml",
}


def detect_text_based_extension(text):
    text = text.strip()

    if text.startswith("#!") and "python" in text:
        return "py"
    if any(
        k in text
        for k in [
            "def ",
            "class ",
            "import ",
            "from ",
            "__main__",
        ]
    ):
        return "py"

    if text.startswith("#!") and ("sh" in text or "bash" in text):
        return "sh"

    if text.startswith("# ") or text.startswith("## ") or "---" in text:
        return "md"

    if text.startswith("---") or (": " in text and "\n" in text):
        return "yaml"

    if "=" in text and "[" in text and "]" in text:
        return "toml"

    if text.startswith("[") and "]" in text:
        return "ini"

    if any(
        text.lower().startswith(cmd)
        for cmd in [
            "select ",
            "insert ",
            "update ",
            "delete ",
            "create ",
        ]
    ):
        return "sql"

    if "{" in text and "}" in text and ":" in text:
        return "css"

    if "," in text and "\n" in text:
        return "csv"

    if text.startswith("<?xml"):
        return "xml"

    return None


def detect_extension(path, mime_type):
    if mime_type in MIME_TO_EXT:
        return MIME_TO_EXT[mime_type]

    if mime_type == "text/plain":
        try:
            with open(path, errors="ignore") as f:
                sample = f.read(4096)
            guessed = detect_text_based_extension(sample)
            if guessed:
                return guessed
        except:
            pass

    return None


def safe_rename(src, dst):
    if not os.path.exists(dst):
        os.rename(src, dst)
        return dst

    base, ext = os.path.splitext(dst)
    counter = 1

    new_path = f"{base} ({counter}){ext}"
    while os.path.exists(new_path):
        counter += 1
        new_path = f"{base} ({counter}){ext}"

    os.rename(src, new_path)
    return new_path


def correct_file_extension(root="."):
    mime = magic.Magic(mime=True)

    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)

            if os.path.islink(path):
                continue

            try:
                mime_type = mime.from_file(path)
            except:
                print(f"Skipping unreadable: {path}")
                continue

            new_ext = detect_extension(path, mime_type)
            if not new_ext:
                continue

            parts = name.rsplit(".", 1)
            current_ext = parts[1].lower() if len(parts) == 2 else ""

            if current_ext == new_ext:
                continue

            base = parts[0] if len(parts) == 2 else name
            new_name = f"{base}.{new_ext}"
            new_path = os.path.join(dirpath, new_name)

            print(f"Renaming: {name}  →  {new_name}")
            final_path = safe_rename(path, new_path)

            if final_path != new_path:
                print(f" ⚠  Collision detected. Saved as: {os.path.basename(final_path)}")


if __name__ == "__main__":
    correct_file_extension()

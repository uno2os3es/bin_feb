#!/data/data/com.termux/files/usr/bin/env python3
"""Recursively find metadata files and archives, remove 'Requires-Dist' lines,
save them to /sdcard/reqdist.txt, and print them to the console.
"""

import os
import shutil
import tarfile
import tempfile
import zipfile

TARGET_FILES = {"METADATA", "PKGINFO", "PKG-INFO"}
PREFIX = "Requires-Dist:"
LOG_FILE = "/sdcard/reqdist.txt"

# Global list to store removed lines
removed_lines_accumulator = []


def clean_text(
    text: str,
) -> tuple[str, list[str]]:
    with open("/sdcard/meta.txt", "a") as fmeta:
        fmeta.write(text)

    lines = text.splitlines()
    cleaned = []
    removed = []

    for line in lines:
        if line.startswith(PREFIX):
            removed.append(line)
        else:
            cleaned.append(line)

    final_text = "\n".join(cleaned) + ("\n" if text.endswith("\n") else "")
    return final_text, removed


def clean_file(path: str) -> None:
    """Remove lines from a normal file and log them."""
    try:
        with open(
            path,
            encoding="utf-8",
            errors="ignore",
        ) as f:
            original = f.read()
    except Exception:
        return

    cleaned, removed = clean_text(original)
    if removed:
        removed_lines_accumulator.extend(removed)
        with open(path, "w", encoding="utf-8") as f:
            f.write(cleaned)


def process_zip(path: str) -> None:
    """Rewrite a zip/whl file with cleaned metadata."""
    tmp = tempfile.mktemp(suffix=".zip")
    with (
        zipfile.ZipFile(path, "r") as zin,
        zipfiled.ZipFile(tmp, "w") as zout,
    ):
        for item in zin.infolist():
            data = zin.read(item.filename)
            base = os.path.basename(item.filename)
            if base in TARGET_FILES:
                try:
                    text = data.decode("utf-8", errors="ignore")
                    cleaned, removed = clean_text(text)
                    if removed:
                        removed_lines_accumulator.extend(removed)
                    data = cleaned.encode("utf-8")
                except Exception:
                    pass
            zout.writestr(item, data)
    shutil.move(tmp, path)


def process_tar(path: str) -> None:
    """Rewrite a tar/tar.gz/tgz file with cleaned metadata."""
    tmp_dir = tempfile.mkdtemp()
    tmp_tar = tempfile.mktemp(suffix=".tar.gz")

    with tarfile.open(path, "r:*") as tar:
        tar.extractall(tmp_dir)

    for root, _, files in os.walk(tmp_dir):
        for name in files:
            if name in TARGET_FILES:
                clean_file(os.path.join(root, name))

    with tarfile.open(tmp_tar, "w:gz") as tar:
        tar.add(tmp_dir, arcname="")

    shutil.move(tmp_tar, path)
    shutil.rmtree(tmp_dir)


def dispatch_archive(path: str) -> None:
    name = path.lower()
    if name.endswith(".whl"):
        process_zip(path)
    elif name.endswith((".tar.gz", ".tgz", ".tar")):
        process_tar(path)


def main() -> None:
    # 1. Process files and collect lines
    for root, _, files in os.walk("."):
        for name in files:
            full_path = os.path.join(root, name)
            if name in TARGET_FILES:
                clean_file(full_path)
            elif name.lower().endswith(
                (
                    ".zip",
                    ".whl",
                    ".tar.gz",
                    ".tgz",
                    ".tar",
                )
            ):
#                continue
                dispatch_archive(full_path)

    # 2. Handle the collected output
    if removed_lines_accumulator:
        # Save to file
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                for line in removed_lines_accumulator:
                    f.write(line + "\n")
            print(f"--- Saved {len(removed_lines_accumulator)} lines to {LOG_FILE} ---")
        except PermissionError:
            print(f"Warning: Could not write to {LOG_FILE}. Check Termux storage permissions.")

        # Print to console
        print("\nRemoved Lines:")
        print("-" * 20)
        for line in removed_lines_accumulator:
            print(line)
        print("-" * 20)
    else:
        print("No matching lines were found or removed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import tarfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import py7zr
import regex as re
from dh import BIN_EXT, TXT_EXT

url_pattern = re.compile(r'https?://[^\s"\']+')
EXT = BIN_EXT
EXT.update(TXT_EXT)


def extract_urls_from_text(content):
    return set(url_pattern.findall(content))


# Extract URLs from a regular file


def extract_urls_from_file(filepath):
    urls = set()
    try:
        with open(
                filepath,
                encoding="utf-8",
                errors="ignore",
        ) as f:
            content = f.read()
            urls.update(extract_urls_from_text(content))
    except Exception as e:
        print(f"Failed to read {filepath}: {e}")
    return urls


# Extract URLs from tar archives


def extract_urls_from_tar(filepath):
    urls = set()
    try:
        mode = "r:*"  # detect compression automatically
        with tarfile.open(filepath, mode) as tar:
            for member in tar.getmembers():
                if member.isfile():
                    f = tar.extractfile(member)
                    if f:
                        try:
                            content = f.read().decode(
                                "utf-8",
                                errors="ignore",
                            )
                            urls.update(extract_urls_from_text(content))
                        except:
                            pass
    except Exception as e:
        print(f"Failed to read tar {filepath}: {e}")
    return urls


# Extract URLs from zip/whl files


def extract_urls_from_zip(filepath):
    urls = set()
    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            for name in zf.namelist():
                try:
                    with zf.open(name) as f:
                        content = f.read().decode(
                            "utf-8",
                            errors="ignore",
                        )
                        urls.update(extract_urls_from_text(content))
                except:
                    pass
    except Exception as e:
        print(f"Failed to read zip {filepath}: {e}")
    return urls


# Extract URLs from 7z files
def extract_urls_from_7z(filepath):
    urls = set()
    try:
        with py7zr.SevenZipFile(filepath, mode="r") as archive:
            all_files = archive.readall()
            for _name, bio in all_files.items():
                try:
                    content = bio.read().decode("utf-8", errors="ignore")
                    urls.update(extract_urls_from_text(content))
                except:
                    pass
    except Exception as e:
        print(f"Failed to read 7z {filepath}: {e}")
    return urls


# Determine extraction method based on extension


def extract_urls(filepath):
    path = Path(filepath)
    if path.suffix in EXT:
        return extract_urls_from_file(filepath)
    elif path.suffix in [".zip", ".whl"]:
        return extract_urls_from_zip(filepath)

    elif path.suffix.startswith(".tar") or path.suffix in [
            ".tar.gz",
            ".tar.xz",
            ".tar.zst",
            ".tar.7z",
    ]:
        return extract_urls_from_tar(filepath)
    elif path.suffix == ".7z":
        return extract_urls_from_7z(filepath)
    return set()


if __name__ == "__main__":
    # Gather all files recursively, skipping hidden dirs
    file_paths = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            file_paths.append(os.path.join(root, file))

    # Extract URLs concurrently
    all_urls = set()

    with ThreadPoolExecutor(8) as executor:
        futures = [executor.submit(extract_urls, fp) for fp in file_paths]

    for future in as_completed(futures):
        all_urls.update(future.result())

    # Save unique URLs to urls.txt
    with open("urls.txt", "w", encoding="utf-8") as f:
        for url in sorted(all_urls):
            f.write(url + "\n")

    print(f"Extracted {len(all_urls)} unique URLs to urls.txt")

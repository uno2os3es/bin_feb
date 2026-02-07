#!/data/data/com.termux/files/usr/bin/env python3
import contextlib
from multiprocessing import Pool, cpu_count
import os
import tarfile
import zipfile

import regex as re

OUTPUT_FILE = "gitlinks.txt"

ARCHIVE_EXTENSIONS = (
    ".zip",
    ".whl",
    ".tar.gz",
    ".tgz",
    ".tar.xz",
    ".txz",
)

# Regex that works on **bytes**
GIT_REGEX_BYTES = re.compile(
    rb'(?:https?://|git@|git://)[^\s\'"]+?\.git\b',
    re.IGNORECASE,
)


def extract_git_urls_from_bytes(data: bytes):
    urls = set()
    for match in GIT_REGEX_BYTES.findall(data):
        with contextlib.suppress(Exception):
            urls.add(match.decode("utf-8", errors="ignore"))
    return urls


def process_regular_file(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        return extract_git_urls_from_bytes(data)
    except Exception:
        return set()


def process_zip(path):
    urls = set()
    try:
        with zipfile.ZipFile(path, "r") as z:
            for name in z.namelist():
                try:
                    with z.open(name) as f:
                        data = f.read()
                        urls |= extract_git_urls_from_bytes(data)
                except Exception:
                    continue
    except Exception:
        pass
    return urls


def process_tar(path, mode):
    urls = set()
    try:
        with tarfile.open(path, mode) as t:
            for member in t.getmembers():
                if member.isfile():
                    try:
                        f = t.extractfile(member)
                        if f:
                            data = f.read()
                            urls |= extract_git_urls_from_bytes(data)
                    except Exception:
                        continue
    except Exception:
        pass
    return urls


def process_archive(path):
    lower = path.lower()
    if lower.endswith((".zip", ".whl")):
        return process_zip(path)
    elif lower.endswith((".tar.gz", ".tgz")):
        return process_tar(path, "r:gz")
    elif lower.endswith((".tar.xz", ".txz")):
        return process_tar(path, "r:xz")
    return set()


def worker(path):
    """Worker function for multiprocessing."""
    try:
        if path.lower().endswith(ARCHIVE_EXTENSIONS):
            return process_archive(path)
        return process_regular_file(path)
    except Exception:
        return set()


def collect_files():
    all_files = []
    for root, _dirs, files in os.walk("."):
        for f in files:
            full = os.path.join(root, f)
            all_files.append(full)
    return all_files


def main() -> None:
    files = collect_files()
    print(f"Found {len(files)} files. Using {cpu_count()} CPU cores...")

    found_urls = set()

    with Pool(cpu_count()) as pool:
        for urls in pool.imap_unordered(worker, files):
            if urls:
                found_urls |= urls

    with open(OUTPUT_FILE, "w") as out:
        for url in sorted(found_urls):
            out.write(url + "\n")

    print(f"\nExtracted {len(found_urls)} unique git URLs → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

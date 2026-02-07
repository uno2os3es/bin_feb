#!/data/data/com.termux/files/usr/bin/env python3
from multiprocessing import Pool, cpu_count
import os
import subprocess
import tarfile
import zipfile

import regex as re

OUTPUT_FILE = "/sdcard/gitlinks.txt"

ARCHIVE_EXTENSIONS = (
    ".zip",
    ".whl",
    ".tar.gz",
    ".tgz",
    ".tar.xz",
    ".txz",
)

# Regex for git URLs
GIT_REGEX = re.compile(
    r'(?:https?://|git@|git://)[^\s\'"]+\b',
    re.IGNORECASE,
)

# --- Extraction helpers ----------------------------------------------------


def extract_git_urls_from_text(text: str):
    return set(GIT_REGEX.findall(text))


def use_strings(path):
    """Extract text from binary using `strings`."""
    try:
        out = subprocess.check_output(
            ["strings", "-a", path],
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def process_regular_file(path):
    """Detect binary, use strings; otherwise read normally."""
    try:
        # Read first bytes to detect text/binary
        with open(path, "rb") as f:
            header = f.read(2048)

        if b"\x00" in header:  # binary file detected
            text = use_strings(path)
            return extract_git_urls_from_text(text)

        # Probably a text file
        with open(path, errors="ignore") as f:
            return extract_git_urls_from_text(f.read())

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

                        if b"\x00" in data:
                            # binary content → run strings on raw data
                            # strings can't read stdin directly, so write temp
                            text = subprocess.check_output(
                                ["strings", "-a"],
                                input=data,
                                stderr=subprocess.DEVNULL,
                            ).decode(
                                "utf-8",
                                errors="ignore",
                            )
                        else:
                            text = data.decode(
                                "utf-8",
                                errors="ignore",
                            )

                        urls |= extract_git_urls_from_text(text)

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

                            if b"\x00" in data:
                                text = subprocess.check_output(
                                    [
                                        "strings",
                                        "-a",
                                    ],
                                    input=data,
                                    stderr=subprocess.DEVNULL,
                                ).decode(
                                    "utf-8",
                                    errors="ignore",
                                )
                            else:
                                text = data.decode(
                                    "utf-8",
                                    errors="ignore",
                                )

                            urls |= extract_git_urls_from_text(text)
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


# --- Worker & main ---------------------------------------------------------


def worker(path):
    try:
        if path.lower().endswith(ARCHIVE_EXTENSIONS):
            return process_archive(path)
        else:
            return process_regular_file(path)
    except Exception:
        return set()


def collect_files():
    out = []
    for root, _dirs, files in os.walk("."):
        for f in files:
            out.append(os.path.join(root, f))
    return out


def main() -> None:
    files = collect_files()
    print(f"Found {len(files)} files. Using {cpu_count()} CPU cores...")

    found = set()

    with Pool(cpu_count()) as pool:
        for urls in pool.imap_unordered(worker, files):
            if urls:
                found |= urls

    with open(OUTPUT_FILE, "a") as fp:
        fp.write("\n")
        for url in sorted(found):
            fp.write(url + "\n")

    print(f"\nExtracted {len(found)} unique git URLs → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

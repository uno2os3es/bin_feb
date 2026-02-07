#!/usr/bin/env python3
import argparse
import contextlib
import io
import os
import sys
import tarfile
import tempfile
from time import perf_counter
import zipfile

from dh import is_valid_url
import regex as re

try:
    import zstandard as zstd  # optional, for .tar.zst support
except Exception:
    zstd = None

DEFAULT_MAX_MB = 50
EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
}

# URL regex - captures http and https URLs and excludes trailing punctuation later
URL_RE = re.compile(
    r'(https?://[^\s\'"<>\\)\\(]+)',
    flags=re.IGNORECASE,
)

# Archive suffixes: order matters (longer suffixes first)
ARCHIVE_SUFFIXES = (
    ".tar.gz",
    ".tgz",
    ".tar.xz",
    ".txz",
    ".tar.bz2",
    ".tbz2",
    ".tar.zst",
    ".tar",  # plain tar
    ".zip",
    ".whl",
)

# File extensions considered "text-like" even if no explicit extension
TEXT_MIME_LIKE = {
    ".txt",
    ".md",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".csv",
    ".rst",
    ".htm",
    ".html",
    ".h",
    ".hpp",
}


def should_skip_dir(dirname):
    return any(part in EXCLUDE_DIRS for part in dirname.split(os.sep))


def find_urls_in_text(text):
    found = set()
    for m in URL_RE.findall(text):
        url = m.rstrip(".,;:)]}>\"'")  # strip common trailing punctuation
        if url:
            found.add(url)
    return found


def decode_bytes_to_text(b):
    # try utf-8, fall back to latin-1 so we don't miss URLs in many files
    for enc in ("utf-8", "latin-1", "utf-16"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    # final fallback: ignore errors
    return b.decode("utf-8", errors="ignore")


def scan_bytes_for_urls(b, max_bytes, exts, name_hint=None):
    """
    Scan bytes for URLs. If exts is provided, and name_hint has an extension not in exts, skip.
    """
    if exts is not None and name_hint:
        _, ext = os.path.splitext(name_hint)
        if ext and ext.lower() not in exts:
            return set()
    if len(b) > max_bytes:
        return set()
    text = decode_bytes_to_text(b)
    return find_urls_in_text(text)


def is_archive_name(name):
    nl = name.lower()
    return any(nl.endswith(suf) for suf in ARCHIVE_SUFFIXES)


def open_tar_from_zst_path(path):
    """
    Decompress a .tar.zst file to a temporary file and open it with tarfile.
    Returns an open TarFile object and the temporary file (so caller can close/remove).
    If zstandard is not available, returns (None, None).
    """
    if zstd is None:
        return None, None
    temp = tempfile.TemporaryFile()
    with open(path, "rb") as fh:
        dctx = zstd.ZstdDecompressor()
        # stream-decompress into temp file
        reader = dctx.stream_reader(fh)
        try:
            while True:
                chunk = reader.read(16384)
                if not chunk:
                    break
                temp.write(chunk)
        finally:
            with contextlib.suppress(Exception):
                reader.close()
    temp.seek(0)
    try:
        tf = tarfile.open(fileobj=temp, mode="r:*")
        return tf, temp
    except Exception:
        # cleanup and re-raise or return None
        with contextlib.suppress(Exception):
            temp.close()
        return None, None


def process_zipfile_zipped(
    zipf,
    max_bytes,
    exts,
    found,
    recursion_depth,
    max_recursion,
):
    """
    Iterate members in a ZipFile object, scan regular files, and recursively handle nested archives.
    """
    for zi in zipf.infolist():
        # skip directories
        if zi.is_dir():
            continue
        name = zi.filename
        # skip very large members
        if zi.file_size > max_bytes:
            continue
        try:
            with zipf.open(zi) as member_f:
                b = member_f.read()
        except Exception:
            continue
        # If member is an archive and recursion allowed, handle
        if recursion_depth < max_recursion and is_archive_name(name):
            process_bytes_as_archive(
                b,
                name,
                max_bytes,
                exts,
                found,
                recursion_depth + 1,
                max_recursion,
            )
        else:
            found.update(
                scan_bytes_for_urls(
                    b,
                    max_bytes,
                    exts,
                    name_hint=name,
                )
            )


def process_tarfile_obj(
    tarf,
    max_bytes,
    exts,
    found,
    recursion_depth,
    max_recursion,
):
    for member in tarf.getmembers():
        if not member.isfile():
            continue
        name = member.name
        if member.size > max_bytes:
            continue
        try:
            f = tarf.extractfile(member)
            if f is None:
                continue
            b = f.read()
        except Exception:
            continue
        if recursion_depth < max_recursion and is_archive_name(name):
            process_bytes_as_archive(
                b,
                name,
                max_bytes,
                exts,
                found,
                recursion_depth + 1,
                max_recursion,
            )
        else:
            found.update(
                scan_bytes_for_urls(
                    b,
                    max_bytes,
                    exts,
                    name_hint=name,
                )
            )


def process_bytes_as_archive(
    b,
    name,
    max_bytes,
    exts,
    found,
    recursion_depth=0,
    max_recursion=3,
):
    """
    Given bytes and a filename hint, try to treat bytes as an archive and extract/scan members.
    recursion_depth prevents infinite recursion in nested archives.
    """
    lname = name.lower()
    bio = io.BytesIO(b)
    try:
        if lname.endswith((".zip", ".whl")):
            try:
                with zipfile.ZipFile(bio) as zf:
                    process_zipfile_zipped(
                        zf,
                        max_bytes,
                        exts,
                        found,
                        recursion_depth,
                        max_recursion,
                    )
            except zipfile.BadZipFile:
                # Not a valid zip archive - fall back to scanning as text
                found.update(
                    scan_bytes_for_urls(
                        b,
                        max_bytes,
                        exts,
                        name_hint=name,
                    )
                )
            return
        # Tar formats that tarfile can detect from fileobj
        if any(
            lname.endswith(suf)
            for suf in (
                ".tar",
                ".tar.gz",
                ".tgz",
                ".tar.xz",
                ".txz",
                ".tar.bz2",
                ".tbz2",
            )
        ):
            try:
                bio.seek(0)
                with tarfile.open(fileobj=bio, mode="r:*") as tf:
                    process_tarfile_obj(
                        tf,
                        max_bytes,
                        exts,
                        found,
                        recursion_depth,
                        max_recursion,
                    )
            except tarfile.ReadError:
                found.update(
                    scan_bytes_for_urls(
                        b,
                        max_bytes,
                        exts,
                        name_hint=name,
                    )
                )
            return
        if lname.endswith(".tar.zst"):
            if zstd is None:
                # Can't handle .tar.zst without zstandard; skip treating as archive and scan as text instead.
                found.update(
                    scan_bytes_for_urls(
                        b,
                        max_bytes,
                        exts,
                        name_hint=name,
                    )
                )
                return
            # Decompress bytes with zstandard to temp file and open tar
            try:
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(io.BytesIO(b)) as reader, tempfile.TemporaryFile() as tmpf:
                    while True:
                        chunk = reader.read(16384)
                        if not chunk:
                            break
                        tmpf.write(chunk)
                    tmpf.seek(0)
                    try:
                        with tarfile.open(
                            fileobj=tmpf,
                            mode="r:*",
                        ) as tf:
                            process_tarfile_obj(
                                tf,
                                max_bytes,
                                exts,
                                found,
                                recursion_depth,
                                max_recursion,
                            )
                    except tarfile.ReadError:
                        found.update(
                            scan_bytes_for_urls(
                                b,
                                max_bytes,
                                exts,
                                name_hint=name,
                            )
                        )
                return
            except Exception:
                found.update(
                    scan_bytes_for_urls(
                        b,
                        max_bytes,
                        exts,
                        name_hint=name,
                    )
                )
                return
        # Unknown archive suffix - fallback to scanning as text
        found.update(scan_bytes_for_urls(b, max_bytes, exts, name_hint=name))
    except Exception:
        # Best effort: if anything goes wrong, scan as text
        found.update(scan_bytes_for_urls(b, max_bytes, exts, name_hint=name))


def process_path(
    path,
    max_bytes,
    exts,
    found,
    recursion_limit=999,
):
    """
    Process a filesystem path: if it's a regular file, scan it; if it's a supported archive, open and scan members.
    """
    try:
        size = os.path.getsize(path)
    except Exception:
        return
    if size > max_bytes and not is_archive_name(path):
        return

    lname = path.lower()
    # Directly open zip/tar archives using file path (to avoid loading entire archive into memory)
    try:
        if any(lname.endswith(suf) for suf in (".zip", ".whl")):
            try:
                with zipfile.ZipFile(path) as zf:
                    process_zipfile_zipped(
                        zf,
                        max_bytes,
                        exts,
                        found,
                        0,
                        recursion_limit,
                    )
                return
            except zipfile.BadZipFile:
                # not a zip, fall back to scanning raw file
                pass

        if any(
            lname.endswith(suf)
            for suf in (
                ".tar",
                ".tar.gz",
                ".tgz",
                ".tar.xz",
                ".txz",
                ".tar.bz2",
                ".tbz2",
            )
        ):
            try:
                with tarfile.open(path, mode="r:*") as tf:
                    process_tarfile_obj(
                        tf,
                        max_bytes,
                        exts,
                        found,
                        0,
                        recursion_limit,
                    )
                return
            except (tarfile.ReadError, EOFError):
                pass

        if lname.endswith(".tar.zst"):
            if zstd is None:
                # Can't decompress; fallback to scanning file as text
                try:
                    # attempt to scan as text (probably compressed garbage -> yields no URLs)
                    with open(path, "rb") as fh:
                        b = fh.read(max_bytes + 1)
                        found.update(
                            scan_bytes_for_urls(
                                b,
                                max_bytes,
                                exts,
                                name_hint=path,
                            )
                        )
                except Exception:
                    pass
                return
            tf, tmpf = open_tar_from_zst_path(path)
            if tf is None:
                return
            try:
                process_tarfile_obj(
                    tf,
                    max_bytes,
                    exts,
                    found,
                    0,
                    recursion_limit,
                )
            finally:
                with contextlib.suppress(Exception):
                    tf.close()
                with contextlib.suppress(Exception):
                    tmpf.close()
            return

        # Not a handled archive - treat as regular file
        with open(path, "rb") as fh:
            b = fh.read(max_bytes + 1)
            found.update(
                scan_bytes_for_urls(
                    b,
                    max_bytes,
                    exts,
                    name_hint=path,
                )
            )
    except Exception:
        return


def main():
    start = perf_counter()
    parser = argparse.ArgumentParser(
        description="Find URLs in files and supported archives recursively and save them to a file."
    )
    parser.add_argument(
        "-o",
        "--output",
        default="urls.txt",
        help="Output file (one URL per line).",
    )
    parser.add_argument(
        "-m",
        "--max-mb",
        type=float,
        default=DEFAULT_MAX_MB,
        help=f"Max file/member size to scan in MB (default {DEFAULT_MAX_MB}).",
    )
    parser.add_argument(
        "-e",
        "--extensions",
        default="",
        help="Comma-separated list of file extensions to scan (e.g. .py,.md). If empty, all files are scanned. Applies to archive members too.",
    )
    parser.add_argument(
        "--max-recursion",
        type=int,
        default=999,
        help="Max nested-archive recursion depth (default 999).",
    )
    args = parser.parse_args()

    max_bytes = int(args.max_mb * 1024 * 1024)
    exts = {e.strip().lower() for e in args.extensions.split(",") if e.strip()} if args.extensions else None

    found = set()
    # Walk filesystem
    for root, dirs, files in os.walk(".", topdown=True, followlinks=False):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        if should_skip_dir(root):
            continue
        for fname in files:
            path = os.path.join(root, fname)
            print(f"processing {os.path.relpath(path)}")
            process_path(
                path,
                max_bytes,
                exts,
                found,
                recursion_limit=args.max_recursion,
            )

    sorted_urls = sorted(found)
    try:
        if os.path.exists(args.output):
            print("urls.txt exists. appending new urls")
            with open(args.output, "a", encoding="utf-8") as out:
                out.write("\n\n")
                for u in sorted_urls:
                    if is_valid_url(u):
                        out.write(u + "\n")
        else:
            with open(args.output, "w", encoding="utf-8") as out:
                for u in sorted_urls:
                    if is_valid_url(u):
                        out.write(u + "\n")
        print(f"Wrote {len(sorted_urls)} unique URLs to {args.output}")
        if any(p.endswith(".tar.zst") for p in sorted_urls):
            # (unlikely) this is just a trivial check; no special action
            pass
    except OSError as e:
        print(
            f"Error writing output file: {e}",
            file=sys.stderr,
        )
    print(f"time:{perf_counter() - start}")


if __name__ == "__main__":
    main()

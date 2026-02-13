#!/usr/bin/env python3
"""
Parallel resumable file downloader with pause, resume, and auto-recovery.
"""

import json
import os
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_RETRIES = 5
RETRY_DELAY = 2


class GracefulExit(Exception):
    pass


def _signal_handler(signum, frame):
    raise GracefulExit()


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def head_request(url: str) -> tuple[int, bool]:
    r = requests.head(url, allow_redirects=True, timeout=10)
    r.raise_for_status()
    size = int(r.headers.get("Content-Length", 0))
    ranges = r.headers.get("Accept-Ranges", "") == "bytes"
    if not ranges:
        raise RuntimeError("Server does not support byte-range requests.")
    return size, ranges


def init_files(path: str, size: int):
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.truncate(size)


def load_meta(meta_path: str) -> dict:
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            return json.load(f)
    return {}


def save_meta(meta_path: str, meta: dict):
    tmp = meta_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(meta, f)
    os.replace(tmp, meta_path)


def build_chunks(size: int) -> list[tuple[int, int]]:
    chunks = []
    for i in range(0, size, CHUNK_SIZE):
        end = min(i + CHUNK_SIZE - 1, size - 1)
        chunks.append((i, end))
    return chunks


def download_chunk(
    url: str,
    path: str,
    start: int,
    end: int,
    meta: dict,
    meta_lock: threading.Lock,
):
    downloaded = meta.get(str(start), start)
    if downloaded > end:
        return

    headers = {"Range": f"bytes={downloaded}-{end}"}

    for attempt in range(MAX_RETRIES):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=15) as r:
                r.raise_for_status()
                with open(path, "r+b") as f:
                    f.seek(downloaded)
                    for chunk in r.iter_content(1024 * 64):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                        with meta_lock:
                            meta[str(start)] = downloaded
            return
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY * (attempt + 1))


def download(url: str, output: str, workers: int = 4):
    meta_path = output + ".meta"
    size, _ = head_request(url)
    init_files(output, size)

    meta = load_meta(meta_path)
    meta_lock = threading.Lock()
    chunks = build_chunks(size)

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = []
            for start, end in chunks:
                futures.append(
                    pool.submit(
                        download_chunk,
                        url,
                        output,
                        start,
                        end,
                        meta,
                        meta_lock,
                    )
                )

            for f in as_completed(futures):
                f.result()

    except GracefulExit:
        save_meta(meta_path, meta)
        print("\nPaused. Resume by re-running the script.")
        sys.exit(0)

    save_meta(meta_path, meta)

    if os.path.getsize(output) == size:
        os.remove(meta_path)
        print("Download completed successfully.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python downloader.py <url> <output_file> [workers]")
        sys.exit(1)

    url = sys.argv[1]
    output = sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    download(url, output, workers)

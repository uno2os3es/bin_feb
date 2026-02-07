#!/data/data/com.termux/files/usr/bin/python
# file: get_download_size.py

import argparse
from pathlib import Path
import urllib.error
import urllib.request


def fetch_content_length(url: str) -> int | None:
    """Try to fetch Content-Length via HEAD or partial GET."""
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            length = response.headers.get("Content-Length")
            if length:
                return int(length)
    except urllib.error.HTTPError as e:
        # 405 Method Not Allowed or 403 Forbidden -> fallback
        if e.code not in (405, 403):
            raise

    # Fallback: GET headers only (partial download)
    request = urllib.request.Request(url, method="GET")
    request.add_header("Range", "bytes=0-0")
    with urllib.request.urlopen(request, timeout=10) as response:
        length = response.headers.get("Content-Length")
        return int(length) if length else None


def format_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def process_url(url: str) -> str:
    try:
        size = fetch_content_length(url)
        print(f"{url[:25]}:{size / (1024 * 1024)} mb")
        if size is None:
            return f"{url}\tUnknown"
        return f"{url}\t{format_size(size)}"
    except Exception as exc:
        return f"{url}\tError: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Show download size of a URL or URLs from a file")
    parser.add_argument(
        "input",
        help="Download URL or file containing URLs",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if input_path.is_file():
        # File mode: update each line with size
        lines = input_path.read_text(encoding="utf-8").splitlines()
        updated_lines = [process_url(line.strip()) for line in lines if line.strip()]

        # Overwrite file
        input_path.write_text(
            "\n".join(updated_lines),
            encoding="utf-8",
        )
        print(f"Updated file: {input_path} ({len(updated_lines)} URLs processed)")
    else:
        # Single URL mode
        print(process_url(args.input))


if __name__ == "__main__":
    main()

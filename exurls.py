#!/usr/bin/env python3
import argparse
import os
import sys
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests


def extract_links(url: str):
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag.get("href").strip()
        if href:
            abs_url = urljoin(url, href)
            parsed = urlparse(abs_url)
            if parsed.scheme in ("http", "https"):
                links.add(abs_url)

    return sorted(links)


def split_internal_external(base_url, links):
    base_domain = urlparse(base_url).netloc

    internal = []
    external = []

    for link in links:
        if urlparse(link).netloc == base_domain:
            internal.append(link)
        else:
            external.append(link)

    return internal, external


def save_links(out_dir, name, links):
    path = os.path.join(out_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extract and save all URLs from a webpage")
    parser.add_argument("url", nargs="?", help="Target URL")
    parser.add_argument(
        "-o",
        "--out",
        default="output",
        help="Output directory (default: output)",
    )

    args = parser.parse_args()

    url = args.url or input("Enter URL: ").strip()
    if not url.startswith(("http://", "https://")):
        print(
            "Error: URL must start with http:// or https://",
            file=sys.stderr,
        )
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)

    try:
        links = extract_links(url)
    except Exception as e:
        print(
            f"Failed to fetch or parse URL: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    internal, external = split_internal_external(url, links)

    save_links(args.out, "all_links.txt", links)
    save_links(args.out, "internal_links.txt", internal)
    save_links(args.out, "external_links.txt", external)

    print(f"Total links     : {len(links)}")
    print(f"Internal links  : {len(internal)}")
    print(f"External links  : {len(external)}")
    print(f"Saved to folder : {args.out}")


if __name__ == "__main__":
    main()

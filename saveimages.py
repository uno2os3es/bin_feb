#!/data/data/com.termux/files/usr/bin/env python3
import argparse
import os
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests


def download_image(url, output_dir):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        filename = os.path.join(output_dir, os.path.basename(url))
        with open(filename, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")


def extract_images_from_url(url, output_dir):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        img_tags = soup.find_all("img")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for img in img_tags:
            img_url = img.get("src")
            if img_url:
                img_url = urljoin(url, img_url)
                download_image(img_url, output_dir)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract images from a URL and save them to an output directory.")
    parser.add_argument("url", type=str, help="URL to extract images from")
    parser.add_argument("output_dir", type=str, help="Output directory to save images")
    args = parser.parse_args()
    extract_images_from_url(args.url, args.output_dir)

#!/data/data/com.termux/files/usr/bin/env python3

from collections import deque
from multiprocessing import Pool
from pathlib import Path
from sys import exit
from time import perf_counter

from dh import IMG_EXT
from fastwalk import walk_files
from PIL import Image, ImageFilter, ImageOps
from pytesseract import image_to_string


def preprocess_image(img):
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    threshold = 150
    return img.point(lambda x: 255 if x > threshold else 0)


def extract_text(image_path):
    img = Image.open(image_path)
    img = preprocess_image(img)
    return image_to_string(img, lang="eng", config="--oem 3 --psm 6")


def process_file(fp):
    try:
        text = extract_text(fp)
        if text:
            txtfile = Path(str(fp.parent) + "/" + str(fp.stem) + ".txt")
            txtfile.write_text(text)
            return f"[OK] {txtfile.name} created."
        else:
            return f"{fp.name} : no text"

    except Exception as e:
        return f"[ERROR] {e}"


def main():
    start = perf_counter()
    files = []
    for pth in walk_files("."):
        path = Path(pth)
        if path.is_symlink():
            continue
        if path.is_file() and path.suffix in IMG_EXT:
            files.append(path)

    with Pool(8) as p:
        pending = deque()
        for f in files:
            pending.append(p.apply_async(process_file, (f,)))
            if len(pending) > 16:
                print(pending.popleft().get())
        while pending:
            print(pending.popleft().get())

    print(f"{perf_counter() - start} sec")


if __name__ == "__main__":
    exit(main())

#!/data/data/com.termux/files/usr/bin/env python3

from pathlib import Path
from sys import argv

from dh import IMG_EXT
from PIL import Image, ImageFilter, ImageOps
from pytesseract import image_to_string


def preprocess_image(img):
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    # Reduce noise
    img = img.filter(ImageFilter.MedianFilter(size=3))
    # Binarize (simple threshold)
    threshold = 150
    return img.point(lambda x: 255 if x > threshold else 0)


def extract_text(image_path):
    img = Image.open(image_path)
    img = preprocess_image(img)
    return image_to_string(img, lang="eng", config="--oem 1 --psm 6")


def main() -> None:
    path = Path(argv[1])
    if path.is_symlink():
        return
    if path.suffix not in IMG_EXT:
        return
    print(f"processing {path.name}")
    text = extract_text(path)
    if text:
        txtfile = Path(str(path.parent) + "/" + str(path.stem) + ".txt")
        with open(txtfile, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{txtfile} created.")
    else:
        print("no text")


if __name__ == "__main__":
    main()

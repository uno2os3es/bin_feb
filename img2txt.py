#!/data/data/com.termux/files/usr/bin/env python3
import os
from pathlib import Path

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
    return image_to_string(img, lang="eng", config="--oem 1 --psm 6")


def main() -> None:
    dir = Path().cwd()
    for pth in os.listdir(dir):
        path = Path(pth)
        if path.suffix in {".jpg", ".png"}:
            print(f"processing {path.name}")
            text = extract_text(path)
            if text:
                txtfile = path.with_suffix(".txt")
                with open(txtfile, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"{txtfile} created.")
            else:
                print("no text")


if __name__ == "__main__":
    main()

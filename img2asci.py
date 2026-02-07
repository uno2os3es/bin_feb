#!/data/data/com.termux/files/usr/bin/python
import os

import rignore
from ascii_magic import AsciiArt

IMG_EXT = [".jpg", ".png", ".jpeg"]


def getimg(dir="."):
    img_files = []
    for fpath in rignore.walk(dir):
        if fpath.suffix in IMG_EXT:
            img_files.append(fpath)
    return img_files


def render_ascii(image_path):
    """
    Convert an image to ASCII and render it to the terminal.
    """
    art = AsciiArt.from_image(image_path)
    art.to_terminal(
        columns=os.get_terminal_size().columns,
        width_ratio=2,
        monochrome=False,
    )


def main():
    imfiles = getimg(".")
    if len(imfiles) == 0:
        print("no image found")
        return
    for file in imfiles:
        render_ascii(file)
    print("done")


if __name__ == "__main__":
    main()

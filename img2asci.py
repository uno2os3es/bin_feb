#!/data/data/com.termux/files/usr/bin/env python3
import os
from pathlib import Path

from ascii_magic import AsciiArt
from dh import IMG_EXT


def getimg(dir="."):
    img_files = []
    for pth in walk_filrs(dir):
        path = Path(pth)
        if path.suffix in IMG_EXT:
            img_files.append(path)
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

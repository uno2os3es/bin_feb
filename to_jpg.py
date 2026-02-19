#!/data/data/com.termux/files/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from multiprocessing import Pool
from pathlib import Path

from dh import folder_size, format_size, is_image, unique_path

try:
    import cv2
    import numpy as np

    USE_CV2 = True
except ImportError:
    from PIL import Image

    USE_CV2 = False

IGNORED_DIRS = {
    ".git",
}


def convert_file(file_path: str) -> bool:
    """Convert an image to JPG, handling transparency with a white background."""
    path = Path(file_path)
    if not path.is_file():
        print(f"Skipping: {path.name} (Unsupported format or not a file)")
        return False

    if path.suffix.lower() == ".jpg":
        return True

    output_path = path.with_suffix(".jpg")

    if output_path.exists():
        ouput_path = unique_path(output_path)

    try:
        if USE_CV2:
            img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if img is None:
                print(f"Error: Could not decode {path.name}")
                return False

            if img.shape[2] == 4:
                b, g, r, a = cv2.split(img)
                white_bg = np.full(
                    img.shape[:2],
                    255,
                    dtype=np.uint8,
                )
                alpha = a.astype(float) / 255.0
                img_b = (b.astype(float) * alpha + white_bg.astype(float) * (1 - alpha)).astype(np.uint8)
                img_g = (g.astype(float) * alpha + white_bg.astype(float) * (1 - alpha)).astype(np.uint8)
                img_r = (r.astype(float) * alpha + white_bg.astype(float) * (1 - alpha)).astype(np.uint8)
                final_img = cv2.merge((img_b, img_g, img_r))
            else:
                final_img = img

            success = cv2.imwrite(
                str(output_path),
                final_img,
                [
                    int(cv2.IMWRITE_JPEG_QUALITY),
                    95,
                ],
            )
        else:
            img = Image.open(path)
            if img.mode in ("RGBA", "LA"):
                background = Image.new(
                    "RGB",
                    img.size,
                    (255, 255, 255),
                )
                background.paste(img, mask=img.split()[-1])
                final_img = background
            else:
                final_img = img
            final_img.save(output_path, "JPEG", quality=95)
            success = True

        if success:
            path.unlink()
            print(f"Successfully converted '{path.name}' to jpg.")
            return True
        else:
            print(f"Failed to write '{output_path.name}'")
            return False

    except Exception as e:
        print(f"Error converting '{path.name}': {e}")
        return False


def main() -> None:
    p = argparse.ArgumentParser(description="jpg")
    p.add_argument("files", nargs="*")
    args = p.parse_args()
    start_size = folder_size(".")

    if args.files:
        files = [Path(f) for f in args.files if Path(f).is_file() and is_image(f)]
    else:
        files = [
            f
            for f in Path(".").rglob("*")
            if f.is_file() and is_image(f) and not any(part in IGNORED_DIRS for part in f.parts)
        ]

    if not files:
        print("No image files detected.")
        return

    print(f"converting {len(files)} files...")

    pool = Pool(8)
    pool.imap_unordered(convert_file, files)
    pool.close()
    pool.join()
    end_size = folder_size(".")
    print(f"{format_size(abs(end_size - start_size))}")


if __name__ == "__main__":
    main()

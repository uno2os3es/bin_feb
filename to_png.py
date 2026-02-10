#!/data/data/com.termux/files/usr/bin/python3.12
from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import cv2
    import numpy as np

    USE_CV2 = True
except ImportError:
    from PIL import Image

    USE_CV2 = False

SF = {
    ".png",
    ".bmp",
    ".tiff",
    ".webp",
    ".ico",
    ".jpg",
    ".jpeg",
}
IGNORED_DIRS = {
    ".git",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "node_modules",
}


def convert_file(file_path: str) -> bool:
    """Convert an image to JPG, handling transparency with a white background."""
    path = Path(file_path)

    if not path.is_file() or path.suffix.lower() not in SF:
        print(f"Skipping: {path.name} (Unsupported format or not a file)")
        return False

    # If already JPG, nothing to do
    if path.suffix.lower() ==".png":
        return True

    output_path = path.with_suffix(".png")

    # Ask before overwriting
    if output_path.exists():
        response = input(f"'{output_path.name}' exists. Overwrite? (y/n): ").strip().lower()
        if response != "y":
            return False

    try:
        if USE_CV2:
            # OpenCV logic
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
            # Pillow logic
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
            path.unlink()  # Delete original file
            print(f"Successfully converted '{path.name}' to png.")
            return True
        else:
            print(f"Failed to write '{output_path.name}'")
            return False

    except Exception as e:
        print(f"Error converting '{path.name}': {e}")
        return False


def is_image_file(path: Path) -> bool:
    if path.suffix in SF:
        return True
    return None


def main() -> None:
    p = argparse.ArgumentParser(description="jpg")
    p.add_argument("files", nargs="*")
    args = p.parse_args()
    start_time = time.perf_counter()

    if args.files:
        files = [Path(f) for f in args.files if Path(f).is_file() and is_image_file(Path(f))]
    else:
        files = [
            f
            for f in Path(".").rglob("*")
            if f.is_file() and not any(part in IGNORED_DIRS for part in f.parts) and is_image_file(f)
        ]

    if not files:
        print("No image files detected.")
        return

    print(f"converting {len(files)} files...")

    # Step 2: Parallel Execution
    # map handles the distribution; lambda passes the context
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(convert_file, files))

    # Step 3: Reporting
    changed_count = sum(1 for r in results if r)
    print(f"Done. {changed_count} files modified.")

    duration = time.perf_counter() - start_time
    print(f"Total Runtime: {duration:.4f} seconds")


if __name__ == "__main__":
    main()

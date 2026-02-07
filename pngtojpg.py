#!/data/data/com.termux/files/usr/bin/python
import os

from PIL import Image

# Traverse current directory recursively
for root, _dirs, files in os.walk("."):
    for file in files:
        if file.lower().endswith(".png"):
            png_path = os.path.join(root, file)
            jpg_path = os.path.splitext(png_path)[0] + ".jpg"

            # Convert PNG to JPG
            try:
                img = Image.open(png_path).convert("RGB")
                img.save(jpg_path, "JPEG")
                os.remove(png_path)
                print(f"Converted and deleted: {png_path} -> {jpg_path}")
            except Exception as e:
                print(f"Failed to convert {png_path}: {e}")

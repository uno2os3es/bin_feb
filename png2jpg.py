#!/data/data/com.termux/files/usr/bin/python
import os
import sys

from PIL import Image

# Check if filename is provided
if len(sys.argv) != 2:
    print("Usage: python convert_png_to_jpg.py <filename.png>")
    sys.exit(1)

fname = sys.argv[1]

# Check if file exists and is a PNG
if not os.path.isfile(fname):
    print(f"File {fname} does not exist.")
    sys.exit(1)
if not fname.lower().endswith(".png"):
    print("File must be a PNG.")
    sys.exit(1)

# Open PNG and convert to JPG
img = Image.open(fname).convert("RGB")
jpg_fname = os.path.splitext(fname)[0] + ".jpg"
img.save(jpg_fname, "JPEG")

# Delete original PNG
os.remove(fname)

print(f"Converted {fname} to {jpg_fname} and deleted the original PNG.")

#!/data/data/com.termux/files/usr/bin/python
# === One-cell Colab notebook: export site-packages ===

import os
import shutil
import site
import zipfile
from pathlib import Path

# 1) Mount Google Drive
from google.colab import drive

drive.mount("/content/drive")

# 2) Resolve system site-packages
site_pkgs = Path(site.getsitepackages()[0])

# 3) Output directory
out_dir = Path("/content/drive/MyDrive/wheels")
out_dir.mkdir(parents=True, exist_ok=True)

# 4) Exclusions
EXCLUDE_PREFIXES = ("setuptools", "pip")


def excluded(name: str) -> bool:
    return name.startswith(EXCLUDE_PREFIXES)


copied_files = 0
zipped_dirs = 0

# 5) Iterate top-level entries
for entry in site_pkgs.iterdir():
    name = entry.name

    if excluded(name):
        continue

    # ---- Copy top-level files ----
    if entry.is_file():
        shutil.copy2(entry, out_dir / name)
        copied_files += 1

    # ---- Zip top-level directories ----
    elif entry.is_dir():
        zip_path = out_dir / f"{name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(entry):
                for f in files:
                    if not str(file).endswith(".pyc"):
                        fp = Path(root) / f
                        zf.write(
                            fp,
                            fp.relative_to(site_pkgs),
                        )
        zipped_dirs += 1

# 6) Report
print("Export completed successfully.")
print(f"Site-packages source : {site_pkgs}")
print(f"Output directory     : {out_dir}")
print(f"Top-level files copied : {copied_files}")
print(f"Top-level dirs zipped  : {zipped_dirs}")
print("Excluded packages     : torch, tensorflow")

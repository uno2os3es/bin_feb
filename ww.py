#!/data/data/com.termux/files/usr/bin/env python3
import os
from pathlib import Path
import subprocess

target_dir = Path(os.getcwd())
os.chdir(target_dir.parent)
subprocess.run(
    [
        "wheel",
        "pack",
        str(target_dir),
        "-d",
        "/sdcard/whl",
    ],
    check=False,
)

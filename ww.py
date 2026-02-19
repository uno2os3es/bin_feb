#!/data/data/com.termux/files/usr/bin/env python3
import os
import subprocess
from pathlib import Path

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

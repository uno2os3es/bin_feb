#!/data/data/com.termux/files/usr/bin/env python3
import os
from pathlib import Path

files = [f.name for f in Path(".").glob("*.srt")]


def common_prefix(strings):
    return os.path.commonprefix(strings)


def common_suffix(strings):
    return os.path.commonprefix([s[::-1] for s in strings])[::-1]


prefix = common_prefix(files)
suffix = common_suffix(files)
for f in files:
    p = Path(f)
    core = f[len(prefix) : len(f) - len(suffix)]
    core = core.strip(".")
    new_name = f"{p.stem.split('.')[0]}.{core}{p.suffix}"
    p.rename(new_name)

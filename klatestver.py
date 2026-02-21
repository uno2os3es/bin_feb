#!/data/data/com.termux/files/usr/bin/env python3
import operator
import os
import pathlib

from packaging.version import Version
import regex as re

# Regex to extract name and version from wheel filename
wheel_pattern = re.compile(r"^(?P<name>.+)-(?P<version>\d+(\.\d+)+).*\.txt$")
files = [f for f in os.listdir(".") if f.endswith(".txt")]
packages = {}
for f in files:
    match = wheel_pattern.match(f)
    if not match:
        continue
    name = match.group("name")
    version = Version(match.group("version"))
    if name not in packages:
        packages[name] = []
    packages[name].append((version, f))
for name, versions in packages.items():
    versions.sort(reverse=True, key=operator.itemgetter(0))
    latest = versions[0]
    old = versions[1:]
    for _v, filename in old:
        pathlib.Path(filename).unlink()
        print(f"{filename} removed")

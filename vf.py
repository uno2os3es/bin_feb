#!/data/data/com.termux/files/usr/bin/env python3
import os

import regex as re

whl_directory = "."
# We added support for date-like versions (yyyyMMdd).
whl_pattern = re.compile(
    r"(?P<name>[\w\-]+)-(?P<version>[\d\.]+(?:-\d{8})?)-(?P<python>py3-none-any|cp37-abi3-linux_armv8l|cp312-cp312-linux_armv8l|cp312-cp312-linux_arm|py3-none-linux_armv8l)\.whl"
)


def cleanup_wheels(whl_files):
    deleted_files = 0
    latest_versions = {}
    for file in whl_files:
        match = whl_pattern.match(file)
        if match:
            package_name = match.group("name")
            version = match.group("version")
            python_variant = match.group("python")
            if "-" in version:
                date_part = version.split("-")[-1]
                if package_name not in latest_versions or date_part > latest_versions[package_name][0]:
                    latest_versions[package_name] = (date_part, version)
    for file in whl_files:
        match = whl_pattern.match(file)
        if match:
            package_name = match.group("name")
            version = match.group("version")
            python_variant = match.group("python")
            # For PyCryptodome
            if (package_name == "pycryptodome" and python_variant == "py3-none-any") or (
                package_name == "matplotlib" and python_variant == "py3-none-any"
            ):
                os.remove(os.path.join(whl_directory, file))
                print(f"Deleted: {file}")
                deleted_files += 1
            elif "-" in version:
                date_part = version.split("-")[-1]
                if latest_versions[package_name][0] != date_part:
                    os.remove(os.path.join(whl_directory, file))
                    print(f"Deleted: {file}")
                    deleted_files += 1
    return deleted_files


whl_files = [f for f in os.listdir(whl_directory) if f.endswith(".whl")]
deleted_files = cleanup_wheels(whl_files)
print(f"Number of files deleted: {deleted_files}")

#!/data/data/com.termux/files/usr/bin/env python3
import os

import regex as re

# Directory containing the .whl files
whl_directory = "."

# Regular expression pattern for matching wheel files
# We added support for date-like versions (yyyyMMdd).
whl_pattern = re.compile(
    r"(?P<name>[\w\-]+)-(?P<version>[\d\.]+(?:-\d{8})?)-(?P<python>py3-none-any|cp37-abi3-linux_armv8l|cp312-cp312-linux_armv8l|cp312-cp312-linux_arm|py3-none-linux_armv8l)\.whl"
)

# Function to clean up the .whl files


def cleanup_wheels(whl_files):
    deleted_files = 0
    # Dictionary to track the latest version by name (including date-like versions)
    latest_versions = {}

    # First pass: Find the latest version for date-like versioning
    for file in whl_files:
        match = whl_pattern.match(file)
        if match:
            package_name = match.group("name")
            version = match.group("version")
            python_variant = match.group("python")

            # Track date-based versions
            if "-" in version:  # Date-like version (e.g., 20251103)
                date_part = version.split("-")[-1]  # Extract the date part
                if package_name not in latest_versions or date_part > latest_versions[package_name][0]:
                    latest_versions[package_name] = (date_part, version)

    # Second pass: Clean up non-latest versions or unwanted variants
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

            # For date-like versioning: Keep the latest version based on date
            elif "-" in version:  # Date-like version (e.g., 20251103)
                date_part = version.split("-")[-1]
                # Check if this is not the latest version for this package
                if latest_versions[package_name][0] != date_part:
                    os.remove(os.path.join(whl_directory, file))
                    print(f"Deleted: {file}")
                    deleted_files += 1

    return deleted_files


# Get all .whl files in the directory
whl_files = [f for f in os.listdir(whl_directory) if f.endswith(".whl")]

# Perform cleanup and report number of deleted files
deleted_files = cleanup_wheels(whl_files)

# Output the results
print(f"Number of files deleted: {deleted_files}")

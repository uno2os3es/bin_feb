#!/data/data/com.termux/files/usr/bin/env python3
import os
import subprocess

import regex as re

# Function to get list of installed packages with their sizes


def get_installed_packages():
    installed_packages = []
    result = subprocess.run(
        [
            "dpkg-query",
            "-W",
            "-f=${binary:Package} ${Installed-Size}\n",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        pkg, size = line.split()
        installed_packages.append((pkg, int(size)))
    return installed_packages


# Function to get bash history commands


def get_bash_history():
    history_file = os.path.expanduser("~/.bash_history")
    if not os.path.exists(history_file):
        return []

    with open(history_file) as f:
        return f.read().splitlines()


# Function to find all installed packages mentioned in bash history


def get_used_packages(history, installed_packages):
    used_packages = set()
    package_names = dict(installed_packages)

    # Search for package names in bash history
    for line in history:
        for pkg in package_names:
            if re.search(rf"\b{pkg}\b", line):
                used_packages.add(pkg)

    return used_packages


# Function to exclude build-essential packages


def exclude_build_packages(installed_packages):
    build_essential_packages = {
        "build-essential",
        "gcc",
        "make",
        "libc6-dev",
        "pkg-config",
        "libtool",
        "dpkg-dev",
        "autoconf",
        "automake",
    }
    return [(pkg, size) for pkg, size in installed_packages if pkg not in build_essential_packages]


# Function to suggest largest unused packages


def suggest_unused_packages(installed_packages, used_packages, top_n=200):
    unused_packages = [pkg for pkg in installed_packages if pkg[0] not in used_packages]
    unused_packages = exclude_build_packages(unused_packages)

    # Sort by size (largest first)
    unused_packages.sort(key=lambda x: x[1], reverse=True)

    return unused_packages[:top_n]


def main():
    # Get installed packages
    installed_packages = get_installed_packages()

    # Get bash history
    history = get_bash_history()

    # Get used packages from history
    used_packages = get_used_packages(history, installed_packages)

    # Suggest top 10 largest unused packages
    suggestions = suggest_unused_packages(
        installed_packages,
        used_packages,
        top_n=100,
    )

    print("Top unused packages (sorted by size):")
    for pkg, size in suggestions:
        if ("python" not in str(pkg)) and ("l8b" not in str(pkg)) and ("static" not in str(pkg)):
            print(f"{pkg}: {size / 1024} MB")


if __name__ == "__main__":
    main()

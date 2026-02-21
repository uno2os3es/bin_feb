#!/data/data/com.termux/files/usr/bin/env python3
from collections import defaultdict
import contextlib
import os
import site

import regex as re


def get_site_packages_dirs():
    dirs = []
    with contextlib.suppress(Exception):
        dirs.extend(site.getsitepackages())
    dirs.append(site.getusersitepackages())
    return list(dict.fromkeys(dirs))


def parse_pkg_info(dirname):
    m = re.match(
        r"(.+)-(\d+.*?)(\.dist-info|\.egg-info)$",
        dirname,
    )
    if m:
        return m.group(1).lower(), m.group(2)
    return None, None


def find_multiple_versions() -> None:
    pkg_versions = defaultdict(set)
    for sp_dir in get_site_packages_dirs():
        if not os.path.isdir(sp_dir):
            continue
        for entry in os.listdir(sp_dir):
            if entry.endswith((".dist-info", ".egg-info")):
                name, version = parse_pkg_info(entry)
                if name:
                    pkg_versions[name].add(version)
    for pkg, versions in sorted(pkg_versions.items()):
        if len(versions) > 1:
            print(f"\nPackage: {pkg}")
            for v in sorted(versions):
                print(f"  - Version: {v}")
    print("\nDone.")


if __name__ == "__main__":
    find_multiple_versions()

#!/data/data/com.termux/files/usr/bin/env python3
import os
import shutil
from packaging.tags import Tag, parse_tag
from packaging.utils import canonicalize_name
from packaging.version import Version


def is_valid_wheel_name(filename):
    try:
        basename = filename[:-4]
        parts = basename.split("-")
        if len(parts) != 5:
            return False

        dist_name, version, build_tag, py_tag, abi_platform = parts

        if not canonicalize_name(dist_name) == dist_name.lower():
            return False

        try:
            Version(version)
        except Exception:
            return False

        if not build_tag[0].isdigit():
            return False

        try:
            parse_tag(py_tag + "-" + abi_platform + "-" + abi_platform.split("-")[-1])
        except Exception:
            return False

        return True
    except Exception:
        return False


def main():
    invalid_dir = "invalid_wheels"
    os.makedirs(invalid_dir, exist_ok=True)

    for filename in os.listdir("."):
        if filename.endswith(".whl"):
            if not is_valid_wheel_name(filename):
                print(f"Invalid wheel name: {filename}")
                shutil.move(filename, os.path.join(invalid_dir, filename))
            else:
                print(f"Valid wheel name: {filename}")


if __name__ == "__main__":
    main()

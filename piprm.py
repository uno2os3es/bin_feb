#!/data/data/com.termux/files/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

# Path to your saved list
PIP_LIST_FILE = "/sdcard/pip.list"

def load_installed_packages():
    """Load installed package names from your saved pip.list"""
    path = Path(PIP_LIST_FILE)
    if not path.exists():
        print(f"{PIP_LIST_FILE} not found")
        sys.exit(1)
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]

def find_dist_info(prefix):
    """Find *.dist-info dirs in site-packages matching the prefix"""
    import site
    matches = []
    for sp in site.getsitepackages():  # system-wide
        sp_path = Path(sp)
        for d in sp_path.glob(f"{prefix}*.dist-info"):
            matches.append(d)
    for sp in site.getusersitepackages(), :  # user site-packages
        sp_path = Path(sp)
        for d in sp_path.glob(f"{prefix}*.dist-info"):
            matches.append(d)
    return matches

def uninstall_packages(packages):
    if not packages:
        print("No packages to uninstall")
        return
    print("Uninstalling:", packages)
    for pkg in packages:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", pkg],
                check=True
            )
            print(f"Uninstalled {pkg}")
        except subprocess.CalledProcessError:
            print(f"Skipped {pkg} (not installed or error)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <package_prefix>")
        sys.exit(1)

    prefix = sys.argv[1].lower()
    installed = load_installed_packages()

    # Filter installed packages by prefix
    to_uninstall = [pkg for pkg in installed if pkg.lower().startswith(prefix)]

    uninstall_packages(to_uninstall)
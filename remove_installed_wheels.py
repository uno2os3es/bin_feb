#!/data/data/com.termux/files/usr/bin/python
import os
import subprocess
import sys
import zipfile

# Path to your virtual environment's 'pip'
VENV_PATH = os.path.expanduser('~/venv')

def get_installed_version(pkg_name):
    try:
        # Use the pip from the venv to get the installed version of the package
        result = subprocess.run([os.path.join(VENV_PATH, 'bin', 'pip'), 'show', pkg_name], capture_output=True, text=True)
        if result.returncode == 0:
            # Extract the version from the pip show output
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    return line.split(":")[1].strip()
    except Exception as e:
        print(f"Error checking installed version for {pkg_name}: {e}")
    return None

def get_wheel_package_info(wheel_file):
    try:
        # Open the .whl file as a zip to extract the package metadata
        with zipfile.ZipFile(wheel_file, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith('METADATA'):
                    with zip_ref.open(file) as f:
                        metadata = f.read().decode('utf-8')
                        # Extract the package name and version from the METADATA file
                        for line in metadata.splitlines():
                            if line.startswith('Name:'):
                                pkg_name = line.split(':')[1].strip()
                            if line.startswith('Version:'):
                                pkg_version = line.split(':')[1].strip()
                        return pkg_name, pkg_version
    except Exception as e:
        print(f"Error reading {wheel_file}: {e}")
    return None, None

def remove_wheel_file(wheel_file):
    try:
        os.remove(wheel_file)
        print(f"Removed: {wheel_file}")
    except Exception as e:
        print(f"Error removing {wheel_file}: {e}")

def main():
    whl_dir = '/sdcard/whl'
    if not os.path.exists(whl_dir):
        print(f"Directory {whl_dir} does not exist.")
        return

    # Loop through all .whl files in the specified directory
    for file in os.listdir(whl_dir):
        if file.endswith(".whl"):
            wheel_file = os.path.join(whl_dir, file)
            pkg_name, pkg_version = get_wheel_package_info(wheel_file)
            if pkg_name and pkg_version:
                installed_version = get_installed_version(pkg_name)
                if installed_version:
                    if installed_version == pkg_version:
                        print(f"{pkg_name} {pkg_version} is already installed in the venv, removing {wheel_file}")
                        remove_wheel_file(wheel_file)
                    elif installed_version > pkg_version:
                        print(f"{pkg_name} {installed_version} is newer than {pkg_version} in venv, removing {wheel_file}")
                        remove_wheel_file(wheel_file)
                    else:
                        print(f"{pkg_name} {pkg_version} is newer than the installed version {installed_version} in venv. Keeping {wheel_file}")
                else:
                    print(f"{pkg_name} is not installed in the venv, keeping {wheel_file}")
            else:
                print(f"Could not extract info from {wheel_file}")

if __name__ == "__main__":
    main()
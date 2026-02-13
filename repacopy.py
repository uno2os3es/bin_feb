#!/data/data/com.termux/files/usr/bin/env python
"""
Automated Python package file collector
Finds site-packages in virtual environments within the current directory,
then copies package files into a wheel-like structure in ~/tmp/repack
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class PackageRepacker:

    def __init__(self, output_base: str = "~/tmp/repack"):
        self.output_base = Path(output_base).expanduser()
        self.output_base.mkdir(parents=True, exist_ok=True)
        self.found_site_packages: list[Path] = []

    def find_site_packages_dirs(self, ) -> list[Path]:
        """Find all site-packages directories starting from the current directory"""
        site_packages_dirs = []

        # Scan only the current directory
        search_paths = [
            Path.cwd(),
        ]

        # Look for virtual environments in common locations
        venv_patterns = [
            ".venv",
            "venv",
            "env",
            "virtualenv",
        ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            try:
                # Look for virtual environments
                for pattern in venv_patterns:
                    # rglob will search recursively from the current directory
                    for venv_dir in search_path.rglob(pattern):
                        if venv_dir.is_dir():
                            # Check for site-packages in virtual environment
                            possible_paths = [
                                venv_dir / "lib" / "python*" / "site-packages",
                                venv_dir / "lib" / "site-packages",
                                venv_dir / "Lib" /
                                "site-packages",  # Windows style, just in case
                            ]

                            for possible_path in possible_paths:
                                for site_pkg in possible_path.parent.glob(
                                        possible_path.name):
                                    if site_pkg.exists() and site_pkg.is_dir():
                                        if site_pkg not in site_packages_dirs:
                                            site_packages_dirs.append(site_pkg)
                                            logger.info(
                                                f"Found virtualenv site-packages: {site_pkg}"
                                            )

                # Look for site-packages directly (e.g., if running inside a venv)
                for site_pkg in search_path.rglob("site-packages"):
                    if site_pkg.is_dir(
                    ) and site_pkg not in site_packages_dirs:
                        site_packages_dirs.append(site_pkg)
                        logger.info(f"Found site-packages: {site_pkg}")

                # Look for dist-packages (Debian/Ubuntu)
                for dist_pkg in search_path.rglob("dist-packages"):
                    if dist_pkg.is_dir(
                    ) and dist_pkg not in site_packages_dirs:
                        site_packages_dirs.append(dist_pkg)
                        logger.info(f"Found dist-packages: {dist_pkg}")

            except (
                    PermissionError,
                    OSError,
            ) as e:
                logger.debug(f"Permission denied scanning {search_path}: {e}")

        # The --skip-scan option will still use the site module for the *current* env,
        # but this default scan is now limited to Path.cwd()

        # Remove duplicates and sort
        unique_dirs = list(set(site_packages_dirs))
        unique_dirs.sort()

        self.found_site_packages = unique_dirs
        return unique_dirs

    def get_package_info_from_dist_info(self, dist_info_dir: Path) -> dict:
        """Extract package metadata from dist-info directory"""
        metadata = {
            "name": dist_info_dir.name.split("-")[0],
            "version": None,
            "requires_python": None,
            "dependencies": [],
        }

        # Try to get version from directory name (format: package-name-version.dist-info)
        parts = dist_info_dir.stem.split("-")  # .stem removes .dist-info
        if len(parts) >= 2:
            metadata["version"] = parts[-1]

        # Read METADATA file for more information
        metadata_file = dist_info_dir / "METADATA"
        if metadata_file.exists():
            try:
                with open(
                        metadata_file,
                        encoding="utf-8",
                ) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("Version:"):
                            metadata["version"] = line.split(":", 1)[1].strip()
                        elif line.startswith("Requires-Python:"):
                            metadata["requires_python"] = line.split(
                                ":", 1)[1].strip()
                        elif line.startswith("Requires-Dist:"):
                            dep = line.split(":", 1)[1].strip()
                            metadata["dependencies"].append(dep)
            except Exception as e:
                logger.warning(
                    f"Could not read metadata from {metadata_file}: {e}")

        return metadata

    def create_wheel_structure(
        self,
        package_name: str,
        metadata: dict,
        files: list[Path],
        site_packages_path: Path,
        base_output_dir: Path,
        original_dist_info_dir: Path,
        is_pure_python: bool,
    ) -> Path | None:
        """Create proper wheel structure in base_output_dir"""

        version = metadata["version"] or "0.0.0"

        if is_pure_python:
            python_tag = "py3"
            abi_tag = "none"
            platform_tag = "any"
            root_is_purelib = "true"
        else:
            logger.info(
                f"Detected C extensions for {package_name}; generating platform-specific tags."
            )
            root_is_purelib = "false"
            try:
                # Use 'packaging' library for the most accurate tags
                from packaging.tags import sys_tags

                best_tag = next(sys_tags())  # Get the first, most specific tag
                python_tag = best_tag.interpreter
                abi_tag = best_tag.abi
                platform_tag = best_tag.platform
                logger.debug(
                    f"Using 'packaging' lib. Tags: {python_tag}-{abi_tag}-{platform_tag}"
                )
            except ImportError:
                # Fallback if 'packaging' is not installed
                logger.warning(
                    "`packaging` library not found. (Install with: pip install packaging)"
                )
                logger.warning(
                    "Falling back to best-guess tags based on current system.")
                import platform

                python_ver = sys.version_info
                python_tag = f"cp{python_ver.major}{python_ver.minor}"
                abi_tag = python_tag  # Best guess for modern CPython
                # e.g., "linux_aarch64"
                platform_tag = f"{platform.system().lower()} _{platform.machine()} "
                logger.debug(
                    f"Fallback tags: {python_tag}-{abi_tag}-{platform_tag}")

        wheel_name = f"{package_name.replace('-', '_')} -{version} -{python_tag} -{abi_tag} -{platform_tag} "
        wheel_dir = base_output_dir / wheel_name

        # Create wheel structure
        dist_info_dir = wheel_dir / f"{package_name}-{version}.dist-info"
        wheel_dir / f"{package_name}-{version}.data"

        dist_info_dir.mkdir(parents=True, exist_ok=True)

        # Copy files to appropriate locations
        for file_path in files:  # file_path is already the relative path from site-packages
            relative_path = file_path

            target_path: Path

            # Check if it's a dist-info file
            if ".dist-info" in str(relative_path):
                # It's a file like 'package-version.dist-info/METADATA'
                # We want to put it in our *new* dist_info_dir
                target_path = dist_info_dir / relative_path.name
            else:
                # It's a regular package file (e.g., 'requests/__init__.py' or 'lxml/etree.so')
                # These go in the root of the wheel structure
                target_path = wheel_dir / relative_path

            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Source path is the file in the *original* site-packages
            source_path = site_packages_path / file_path

            if source_path.exists():
                shutil.copy2(source_path, target_path)
            else:
                logger.warning(f"File from RECORD not found at {source_path}")

        # Create WHEEL file
        wheel_file = dist_info_dir / "WHEEL"
        with open(wheel_file, "w") as f:
            f.write("Wheel-Version: 1.0\n")
            f.write("Generator: auto-repacker 1.0\n")
            f.write(f"Root-Is-Purelib: {root_is_purelib}\n")  # <-- Updated
            # <-- Updated
            f.write(f"Tag: {python_tag}-{abi_tag}-{platform_tag}\n")

        # Copy METADATA file if it wasn't in RECORD (as a fallback)
        original_metadata = original_dist_info_dir / "METADATA"
        new_metadata_path = dist_info_dir / "METADATA"
        if not new_metadata_path.exists() and original_metadata.exists():
            shutil.copy2(
                original_metadata,
                new_metadata_path,
            )
        elif not new_metadata_path.exists():
            # Create basic metadata
            with open(new_metadata_path, "w") as f:
                f.write("Metadata-Version: 2.1\n")
                f.write(f"Name: {package_name}\n")
                f.write(f"Version: {version}\n")

        # Copy original RECORD file (with correct hashes)
        original_record = original_dist_info_dir / "RECORD"
        if original_record.exists():
            shutil.copy2(
                original_record,
                dist_info_dir / "RECORD",
            )
        else:
            logger.warning(
                f"Could not find original RECORD file at {original_record}")

        return wheel_dir

    def copy_package_files(
        self,
        dist_info_dir: Path,
        site_packages_path: Path,
        output_dir: Path,
    ) -> bool:
        """Copies all files for a single package into a wheel structure directory"""
        try:
            record_file = dist_info_dir / "RECORD"
            if not record_file.exists():
                logger.warning(
                    f"Skipping {dist_info_dir.name}: RECORD file not found")
                return False

            # Get package metadata
            metadata = self.get_package_info_from_dist_info(dist_info_dir)
            package_name = metadata["name"]

            if not package_name:
                logger.warning(
                    f"Could not determine package name for {dist_info_dir}")
                return False

            # Read files from RECORD and check for C extensions
            files_to_include = []
            is_pure_python = True
            with open(record_file, encoding="utf-8") as f:
                for line in f:
                    file_path_str = line.split(",")[0].strip()
                    # Include all files from RECORD, except the RECORD file itself
                    if file_path_str and not file_path_str.endswith(
                            ".dist-info/RECORD"):
                        # Check for C extensions
                        if file_path_str.endswith(".so"):
                            is_pure_python = False

                        full_path = site_packages_path / file_path_str
                        if full_path.exists():
                            files_to_include.append(Path(file_path_str))

            if not files_to_include:
                logger.warning(f"No files found for package {package_name}")
                return False

            # Create wheel structure directly in the output directory
            package_structure_path = self.create_wheel_structure(
                package_name,
                metadata,
                files_to_include,
                site_packages_path,
                output_dir,
                dist_info_dir,
                is_pure_python,  # <-- Pass the purity flag
            )

            if package_structure_path:
                logger.info(
                    f"Copied package files to: {package_structure_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error copying files for {dist_info_dir.name}: {e}")
            return False

    def copy_all_packages(self):
        """Copies all packages found in all site-packages directories"""
        total_copied = 0

        for site_packages_dir in self.found_site_packages:
            logger.info(f"Processing site-packages: {site_packages_dir}")

            # Create output subdirectory for this site-packages
            env_name = "local_env"
            try:
                # Try to guess env name from path
                if (".venv" in str(site_packages_dir)
                        or "venv" in str(site_packages_dir)
                        or "env" in str(site_packages_dir)):
                    env_name = site_packages_dir.parent.parent.name
            except Exception:
                pass  # stick with 'local_env'

            output_dir = self.output_base / env_name
            output_dir.mkdir(parents=True, exist_ok=True)

            # Find all dist-info directories
            dist_info_dirs = list(site_packages_dir.glob("*.dist-info"))
            package_count = 0

            for dist_info_dir in dist_info_dirs:
                if dist_info_dir.is_dir() and self.copy_package_files(
                        dist_info_dir,
                        site_packages_dir,
                        output_dir,
                ):
                    package_count += 1
                    total_copied += 1

            logger.info(
                f"Copied {package_count} packages from {site_packages_dir}")

        logger.info(f"Total packages copied: {total_copied}")
        logger.info(f"Package files saved to: {self.output_base}")


def main():
    parser = argparse.ArgumentParser(
        description=
        "Automatically find and copy Python packages to a wheel structure")
    parser.add_argument(
        "--output",
        "-o",
        default="~/tmp/repack",
        help="Output directory (default: ~/tmp/repack)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--skip-scan",
        action="store_true",
        help="Skip local scan and use current active environment only",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        repacker = PackageRepacker(output_base=args.output)

        if args.skip_scan:
            # Use current environment only
            import site

            current_site_packages = site.getsitepackages()
            user_site = site.getusersitepackages()
            if user_site:
                current_site_packages.append(user_site)

            repacker.found_site_packages = [
                Path(p) for p in current_site_packages if Path(p).exists()
            ]
            logger.info(
                f"Using current active environment site-packages: {repacker.found_site_packages}"
            )
        else:
            # Scan current directory for all site-packages
            logger.info(
                "Scanning current directory for site-packages directories...")
            site_packages_dirs = repacker.find_site_packages_dirs()
            logger.info(
                f"Found {len(site_packages_dirs)} site-packages directories")

        if not repacker.found_site_packages:
            logger.error("No site-packages directories found!")
            return 1

        # Repack all packages
        repacker.copy_all_packages()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

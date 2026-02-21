#!/usr/bin/env python3
"""
Advanced Pip Package Uninstaller - Using pip's internal API with version compatibility
"""

import sys
import warnings

# Suppress pip's internal deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


def get_pip_api():
    """Try to import pip's API with fallbacks for different versions"""
    try:
        # Try the modern pip API first
        from pip._internal.cli.main import main as pip_main
        from pip._internal.metadata import get_default_environment
        from pip._internal.operations.freeze import freeze

        def get_packages():
            """Get packages using modern pip API"""
            try:
                env = get_default_environment()
                return {dist.name: dist.version for dist in env.iter_installed_distributions()}
            except:
                # Fallback to freeze
                packages = {}
                for line in freeze():
                    if "==" in line:
                        name, version = line.split("==", 1)
                        packages[name] = version
                return packages

        def uninstall(packages: list[str]):
            """Uninstall using modern pip API"""
            args = ["uninstall", "-y", *packages]
            return pip_main(args)

        return get_packages, uninstall

    except ImportError:
        try:
            # Fallback to older pip API
            import pip

            def get_packages():
                """Get packages using older pip API"""
                packages = {}
                for dist in pip.get_installed_distributions():
                    packages[dist.project_name] = dist.version
                return packages

            def uninstall(packages: list[str]):
                """Uninstall using older pip API"""
                for pkg in packages:
                    pip.uninstall(pkg)
                return 0

            return get_packages, uninstall

        except ImportError:
            return None, None


def display_packages(packages: dict[str, str], title: str = "Packages"):
    """Display packages in a formatted way"""
    if not packages:
        return

    print(f"\n{title}:")
    for pkg, version in sorted(packages.items()):
        print(f"  - {pkg} (version: {version})")
    print(f"\nTotal: {len(packages)} package(s)")


def find_matching_packages(pattern: str, packages: dict[str, str]) -> dict[str, str]:
    """Find packages that contain the pattern in their name"""
    matches = {}
    pattern_lower = pattern.lower()

    for package_name, version in packages.items():
        if pattern_lower in package_name.lower():
            matches[package_name] = version

    return matches


def main():
    # Check if pattern was provided
    if len(sys.argv) != 2:
        print("Usage: python uninstaller_pip.py <pattern>")
        print("\nExample: python uninstaller_pip.py sphinx")
        print("This will uninstall all packages containing 'sphinx' in their name")
        sys.exit(1)

    pattern = sys.argv[1]

    # Get pip API functions
    get_packages_func, uninstall_func = get_pip_api()

    if not get_packages_func or not uninstall_func:
        print("Error: Could not import pip API. Falling back to subprocess...")
        # Here you could fall back to the subprocess version
        print("Please install pip or use the subprocess version of this script.")
        sys.exit(1)

    print(f"Searching for packages containing '{pattern}'...")

    # Get installed packages
    try:
        installed_packages = get_packages_func()
    except Exception as e:
        print(f"Error getting package list: {e}")
        sys.exit(1)

    if not installed_packages:
        print("No installed packages found.")
        sys.exit(0)

    # Find matching packages
    matching_packages = find_matching_packages(pattern, installed_packages)

    if not matching_packages:
        print(f"No installed packages found containing '{pattern}' in their name.")
        sys.exit(0)

    # Display packages to uninstall
    display_packages(matching_packages, "Packages to uninstall")

    # Ask for confirmation
    response = input("\nDo you want to proceed with uninstallation? (y/N): ").strip().lower()

    if response not in ["y", "yes"]:
        print("Uninstallation cancelled.")
        sys.exit(0)

    # Uninstall packages
    print("\nUninstalling...")
    try:
        result = uninstall_func(list(matching_packages.keys()))

        if result == 0:
            print(f"\n✓ Successfully uninstalled {len(matching_packages)} package(s)")
            sys.exit(0)
        else:
            print(f"\n⚠ Uninstallation completed with return code: {result}")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error during uninstallation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

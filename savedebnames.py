#!/data/data/com.termux/files/usr/bin/python
import subprocess


def save_installed_packages(
    output_file="installed.txt",
):
    """
    Save the names of installed Debian packages to a text file.
    Package names are saved without their version numbers.
    """
    try:
        # Run dpkg-query to get a list of installed packages
        result = subprocess.run(
            [
                "dpkg-query",
                "-f",
                "${binary:Package}\n",
                "-W",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Get the package names from the command output
        installed_packages = result.stdout.splitlines()

        # Write package names to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(installed_packages))

        print(f"Installed package names saved to '{output_file}'")
    except FileNotFoundError:
        print("Error: dpkg-query command not found. Are you running this script on a Debian-based system?")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to retrieve installed packages. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    save_installed_packages()

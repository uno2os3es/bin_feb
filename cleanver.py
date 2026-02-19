#!/data/data/com.termux/files/usr/bin/env python3
import subprocess


def create_unpinned_requirements(
    output_file="req.txt",
):
    """Runs pip freeze and saves only package names to output_file."""
    try:
        result = subprocess.run(
            ["pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
        )

        package_names = []
        for line in result.stdout.splitlines():
            if not line or line.startswith("#"):
                continue

            pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].split(" @ ")[0]
            package_names.append(pkg.strip())

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(package_names) + "\n")

        print(f"Successfully saved {len(package_names)} package names to {output_file}.")

    except subprocess.CalledProcessError as e:
        print(f"Error running pip freeze: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    create_unpinned_requirements()

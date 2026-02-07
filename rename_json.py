#!/data/data/com.termux/files/usr/bin/python
import json
import os


def rename_pypi_metadata_files():
    # Get all json files in the current directory
    files = [f for f in os.listdir(".") if f.endswith(".json")]

    for filename in files:
        try:
            with open(filename, encoding="utf-8") as f:
                data = json.load(f)

            # Common PyPI JSON structures use 'info' -> 'name'
            # or it might be at the top level depending on your specific export
            pkg_name = None

            if "info" in data and "name" in data["info"]:
                pkg_name = data["info"]["name"]
            elif "name" in data:
                pkg_name = data["name"]

            if pkg_name:
                # Sanitize name to ensure it's a valid filename
                new_name = f"{pkg_name}.json"

                # Check if the file is already named correctly to avoid errors
                if filename == new_name:
                    print(f"Skipping: {filename} is already correctly named.")
                    continue

                # Rename the file
                os.rename(filename, new_name)
                print(f"Renamed: {filename} -> {new_name}")
            else:
                print(f"Warning: Could not find package name in {filename}")

        except json.JSONDecodeError:
            print(f"Error: {filename} is not a valid JSON file.")
        except Exception as e:
            print(f"An error occurred with {filename}: {e}")


if __name__ == "__main__":
    rename_pypi_metadata_files()

#!/data/data/com.termux/files/usr/bin/env python3
import os


def delete_multiline_string_from_files(search_string, directory=".") -> None:
    # Recursively walk through the directory
    EXT = [
        ".txt",
        ".py",
        ".md",
        ".pyx",
        ".pyi",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
    ]
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)

            # Only process files (skip directories)
            if os.path.isfile(file_path) and os.path.splitext(file_path)[1] in EXT:
                try:
                    with open(
                        file_path,
                        encoding="utf-8",
                    ) as file:
                        content = file.read()

                    # Check if the string to delete exists in the file
                    if search_string in content:
                        # Remove the multiline string from the file
                        new_content = content.replace(search_string, "")

                        with open(file_path, "w") as file:
                            file.write(new_content)
                        print(f"Deleted string from {file_path}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")


def read_string_to_delete(
    filename="/sdcard/todel.txt",
):
    try:
        with open(filename) as file:
            return file.read()
    except Exception as e:
        print(f"Error reading the file {filename}: {e}")
        return None


if __name__ == "__main__":
    string_to_delete = read_string_to_delete()
    if string_to_delete:
        delete_multiline_string_from_files(string_to_delete)

#!/data/data/com.termux/files/usr/bin/env python3
from sys import argv


def remove_spaces_from_file(fname) -> None:
    try:
        with open(fname) as file:
            lines = file.readlines()

        # Strip leading and trailing spaces from each line
        cleaned_lines = [line.lstrip() for line in lines]

        # Optionally, write the cleaned lines back to the file or print
        with open(fname, "w") as file:
            file.writelines("".join(cleaned_lines))

        print(f"{fname} cleaned.")

    except FileNotFoundError:
        print(f"Error: File '{fname}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    remove_spaces_from_file(argv[1])

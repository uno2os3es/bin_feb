#!/data/data/com.termux/files/usr/bin/python
import sys

import regex as re


def clean_line_numbers(input_file, output_file):
    with open(input_file) as infile:
        lines = infile.readlines()

    with open(output_file, "w") as outfile:
        for line in lines:
            # Use regex to remove leading numbers and whitespace
            cleaned_line = re.sub(r"^\s*\d+\s+", "", line)
            outfile.write(cleaned_line)


if __name__ == "__main__":
    input_file = sys.argv[1]  # Replace with your input file name
    output_file = sys.argv[1]  # Replace with your desired output file name
    clean_line_numbers(input_file, output_file)

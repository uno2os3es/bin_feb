#!/data/data/com.termux/files/usr/bin/env python3
import subprocess
import sys


def main():
    input_file = sys.argv[1]
    output_file = input_file.replace(".mkv", ".txt")
    command = f'ffmpeg -y -i "{input_file}" -map 0:s:0 "{output_file}"'
    subprocess.run(command, check=False, shell=True)


if __name__ == "__main__":
    main()

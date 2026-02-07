#!/data/data/com.termux/files/usr/bin/python
import os
import subprocess
import sys

# Get the input file name from the command line argument
if len(sys.argv) != 2:
    print("Usage: python extract_subtitles.py <input_file>")
    sys.exit(1)
input_file = sys.argv[1]
# Create the output directory if it doesn't exist
output_dir = "subtitles"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
# Extract subtitles using ffmpeg
command = f"ffmpeg -i {input_file} -map_metadata:s:0 {output_dir}/subtitles.srt"
subprocess.run(command, check=False, shell=True)
print("Subtitles extracted")

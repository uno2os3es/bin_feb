#!/data/data/com.termux/files/usr/bin/python
import os
import subprocess


def extract_subtitles(input_file, output_file=None, subtitle_index=0):
    """
    Extract subtitles from an MKV file using FFmpeg.

    :param input_file: Path to the input MKV file.
    :param output_file: Path to save the subtitle file. If None, uses input filename with .srt extension.
    :param subtitle_index: Index of the subtitle track to extract (default: 0).
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".srt"

    cmd = [
        "ffmpeg", "-i", input_file, "-map", f"0:s:{subtitle_index}", "-y",
        output_file
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Subtitles extracted to: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting subtitles: {e}")


# Example usage
extract_subtitles("your_movie.mkv")

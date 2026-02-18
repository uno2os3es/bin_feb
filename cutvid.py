#!/data/data/com.termux/files/usr/bin/env python3

import argparse
from pathlib import Path
import sys
import regex as re
import ffmpeg


TIME_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}$")


def validate_time(value: str) -> str:
    if not TIME_PATTERN.match(value):
        raise argparse.ArgumentTypeError("Time must be in HH:MM:SS format (e.g. 00:10:00)")
    return value


def hhmmss_to_seconds(t: str) -> int:
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s


def main():
    parser = argparse.ArgumentParser(description="Trim a video using ffmpeg-python (stream copy)")

    parser.add_argument("file", help="Input video file")
    parser.add_argument("start", type=validate_time, help="Start time (HH:MM:SS)")
    parser.add_argument("end", type=validate_time, help="End time (HH:MM:SS)")

    args = parser.parse_args()

    input_path = Path(args.file)

    if not input_path.exists():
        print("Error: file not found.")
        sys.exit(1)

    start_sec = hhmmss_to_seconds(args.start)
    end_sec = hhmmss_to_seconds(args.end)

    if end_sec <= start_sec:
        print("Error: end time must be greater than start time.")
        sys.exit(1)

    duration = end_sec - start_sec

    output_path = input_path.with_name(f"{input_path.stem}_trimmed{input_path.suffix}")

    try:
        (
            ffmpeg.input(str(input_path), ss=args.start, t=duration)
            .output(str(output_path), c="copy", avoid_negative_ts="make_zero")
            .run(overwrite_output=True)
        )

        print(f"Saved: {output_path}")

    except:
        print("FFmpeg error:")
        sys.exit(1)


if __name__ == "__main__":
    main()

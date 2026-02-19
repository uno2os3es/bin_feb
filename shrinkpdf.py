#!/data/data/com.termux/files/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def human_size(num_bytes: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} TB"


def run(cmd: list[str]) -> None:
    """Run command or exit on failure."""
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(
            f"[ERROR] Command failed: {' '.join(cmd)}",
            file=sys.stderr,
        )
        sys.exit(e.returncode)


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} input.pdf")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()

    if not input_path.exists():
        print(
            "Input file not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    if input_path.suffix.lower() != ".pdf":
        print(
            "Input must be a PDF file.",
            file=sys.stderr,
        )
        sys.exit(1)

    temp_gs = input_path.with_name(f"temp_gs_{input_path.name}")

    size_before = input_path.stat().st_size
    print(f"Before : {human_size(size_before)}")

    gs_cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dDownsampleColorImages=true",
        "-dDownsampleGrayImages=true",
        "-dDownsampleMonoImages=true",
        "-dColorImageResolution=50",
        "-dGrayImageResolution=50",
        "-dMonoImageResolution=50",
        "-dColorImageDownsampleType=/Bicubic",
        "-dGrayImageDownsampleType=/Bicubic",
        "-dMonoImageDownsampleType=/Subsample",
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        f"-sOutputFile={temp_gs}",
        str(input_path),
    ]

    run(gs_cmd)

    size_after = temp_gs.stat().st_size
    print(f"After  : {human_size(size_after)}")

    diff = size_before - size_after
    sign = "-" if diff >= 0 else "+"

    if size_after < size_before:
        temp_gs.replace(input_path)
        print(f"Saved  : {sign}{human_size(abs(diff))}")
    else:
        print("original file is smaller")
        temp_gs.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

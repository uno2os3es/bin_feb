#!/data/data/com.termux/files/usr/bin/env python3
import glob
import subprocess
from multiprocessing import Pool
from pathlib import Path

QUALITY_RANGE = "60-70"
START_DIR = Path(".")
NUM_PROCESSES = 8
print(
    f"Using {NUM_PROCESSES} CPU cores for parallel processing via subprocess.")


def process_png(input_path):
    try:
        command = [
            "pngquant",
            f"--quality={QUALITY_RANGE}",
            "--force",  # Force overwrite
            # Do not save if file size increases (safe optimization)
            "--skip-if-larger",
            input_path,
            "--output",
            input_path,  # Overwrite the original file
        ]
        # Execute the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        if "skipping" in result.stdout.lower():
            print(
                f"🟢 Skipped: {input_path} (No size reduction possible or quality too low)"
            )
        else:
            print(f"✅ Optimized: {input_path} (Quality: {quality_range})")
    except subprocess.CalledProcessError as e:
        print(
            f"❌ Error compressing {input_path} via subprocess. Return Code: {e.returncode}. Error: {e.stderr.strip()}"
        )
    except FileNotFoundError:
        print(
            "❌ Error: 'pngquant' command not found. Please ensure the 'pngquant' binary is installed and in your system PATH."
        )
    except Exception as e:
        print(f"❌ Error compressing {input_path}: {e}")


if __name__ == "__main__":
    files = glob.glob(
        str(START_DIR / "**" / "*.png"),
        recursive=True,
    )
    if not files:
        print(f"No PNG files found recursively in {START_DIR}.")
    else:
        print(f"Found {len(files)} PNG files to process...")
        with Pool(8) as pool:
            for f in files:
                pool.apply_async(process_png, (f, ))

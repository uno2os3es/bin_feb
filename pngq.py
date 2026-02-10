#!/data/data/com.termux/files/usr/bin/env python3
import glob
import subprocess
from functools import partial
from multiprocessing import Pool, cpu_count
from pathlib import Path

# --- Configuration ---
QUALITY_RANGE_STR = "60-70"
START_DIR = Path(".")
NUM_PROCESSES = cpu_count()
print(f"Using {NUM_PROCESSES} CPU cores for parallel processing via subprocess.")

# --- Optimization Function (Subprocess) ---


def compress_single_file_subprocess(input_path: str, quality_range: str):
    """
    Compresses a single PNG file by directly calling the pngquant CLI
    using the subprocess module. This avoids all Python wrapper API issues.
    """
    try:
        # Construct the command:
        # pngquant --quality=60-70 --force --skip-if-larger input_path.png --output input_path.png
        command = [
            "pngquant",
            f"--quality={quality_range}",
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
            print(f"🟢 Skipped: {input_path} (No size reduction possible or quality too low)")
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


# --- Main Execution (Switch to subprocess function) ---
if __name__ == "__main__":
    all_png_files = glob.glob(
        str(START_DIR / "**" / "*.png"),
        recursive=True,
    )
    if not all_png_files:
        print(f"No PNG files found recursively in {START_DIR}.")
    else:
        print(f"Found {len(all_png_files)} PNG files to process...")
        # Use functools.partial to pre-set the quality argument
        compress_task = partial(
            compress_single_file_subprocess,
            quality_range=QUALITY_RANGE_STR,
        )
        # Create a multiprocessing Pool
        try:
            with Pool(NUM_PROCESSES) as pool:
                pool.map(compress_task, all_png_files)
            print("\n✨ All PNG files processed successfully using Subprocess. ✨")
        except Exception as e:
            print(f"\nAn unexpected error occurred during multiprocessing: {e}")

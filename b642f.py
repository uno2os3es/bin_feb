#!/data/data/com.termux/files/usr/bin/env python3
# b64_to_files.py
import base64
import sys
from pathlib import Path


def decode_base64_lines(input_txt_path, output_folder="decoded_files"):
    """
    Reads a text file where each line is a base64 string,
    decodes it and saves each result to a separate file.
    """
    # Create output folder if it doesn't exist
    output_dir = Path(output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Counters
    success_count = 0
    error_count = 0

    try:
        with open(input_txt_path, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue  # skip empty lines

                try:
                    # Decode base64 → bytes
                    decoded_bytes = base64.b64decode(line.strip())

                    # Choose output filename (you can customize the naming pattern)
                    output_filename = f"decoded_{i:04d}.bin"  # .bin is safe default
                    # Alternative examples:
                    # output_filename = f"file_{i}.txt"           # if you know it's text
                    # output_filename = f"image_{i}.png"          # if you know it's PNGs
                    # output_filename = f"data_{i}.dat"

                    output_path = output_dir / output_filename

                    # Write the decoded bytes
                    with open(output_path, "wb") as out_file:
                        out_file.write(decoded_bytes)

                    print(f"✓ Line {i:4d} → {output_path}")
                    success_count += 1

                except Exception as e:
                    print(f"✗ Line {i:4d} failed: {e}")
                    error_count += 1
                    # Optional: save failed lines somewhere
                    # with open("failed_lines.txt", "a") as ferr:
                    #     ferr.write(f"{line}\n")

        print("\n" + "=" * 50)
        print("Finished!")
        print(f"Successfully decoded: {success_count} files")
        print(f"Failed            : {error_count} lines")
        if success_count > 0:
            print(f"Files saved in: {output_dir.resolve()}")

    except FileNotFoundError:
        print(f"Error: Input file not found: {input_txt_path}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    # ← Change this to your actual file path
    INPUT_FILE = sys.argv[1]

    # Optional: change output folder name
    OUTPUT_FOLDER = "decoded_output"

    decode_base64_lines(INPUT_FILE, OUTPUT_FOLDER)

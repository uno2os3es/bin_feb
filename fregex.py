#!/data/data/com.termux/files/usr/bin/python
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import regex as re
from tqdm import tqdm  # For a progress bar. Install it using `pip install tqdm`


def extract_regex_patterns(file_path):
    """
    Extracts regex patterns from a Python file.
    Returns a list of patterns (strings).
    """
    patterns = []
    regex_pattern = re.compile(r're\.(compile|search|match|findall|fullmatch|finditer)\(\s*([rR]?[\'"])(.*?)(?<!\\)\2')
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        patterns = regex_pattern.findall(content)
    except (OSError, UnicodeDecodeError):
        pass  # Skip unreadable files
    return [match[2] for match in patterns]


def process_file(file_path, output_dir):
    """
    Process a single file to extract regex, then save to a corresponding output file.
    """
    patterns = extract_regex_patterns(file_path)
    if patterns:
        relative_path = os.path.relpath(file_path, os.getcwd())
        output_file = output_dir / f"{relative_path.replace(os.sep, '_')}.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(patterns))
    return file_path, len(patterns)


def find_regex_in_dir(start_dir, output_dir, max_workers=4):
    """
    Scans for all regex patterns in Python files in parallel using ThreadPoolExecutor.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files_to_process = [
        os.path.join(root, fname) for root, _, files in os.walk(start_dir) for fname in files if fname.endswith(".py")
    ]

    total_files = len(files_to_process)
    progress_bar = tqdm(
        total=total_files,
        desc="Progress",
        unit="file",
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(
                process_file,
                file_path,
                output_dir,
            ): file_path
            for file_path in files_to_process
        }

        processed_files = 0
        for future in as_completed(futures):
            _, regex_count = future.result()
            if regex_count:
                print(f"Processed file '{futures[future]}' with {regex_count} regex patterns.")
            processed_files += 1
            progress_bar.update(1)

    progress_bar.close()
    print(f"Scanning complete. Processed {total_files} files.")


if __name__ == "__main__":
    output_directory = "output"
    find_regex_in_dir(
        os.getcwd(),
        output_directory,
        max_workers=4,
    )
    print(f"Regex extraction complete. Results saved in {output_directory}")

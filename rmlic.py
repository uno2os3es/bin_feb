#!/usr/bin/env python3
from multiprocessing import Pool, cpu_count
from pathlib import Path

import regex as re
from dh import BIN_EXT, TXT_EXT, is_binary

# -------- CONFIG --------
LIC_FILE = Path("/sdcard/lic")
MIN_BLANK_LINES = 3  # Minimum blank lines to separate patterns
NUM_WORKERS = max(cpu_count(), 8)
EXCLUDE_EXTS = BIN_EXT
# ------------------------


def load_patterns(lic_path: Path) -> list[str]:
    """Load multiline patterns from the license file."""
    try:
        with open(lic_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Split by 3 or more consecutive blank lines
        # Pattern: \n followed by 3+ groups of (optional spaces + \n)
        pattern_separator = r"\n(?:\s*\n){" + str(MIN_BLANK_LINES) + r",}"
        patterns = re.split(pattern_separator, content)

        # Clean up patterns: strip whitespace and filter empty ones
        patterns = [p.strip() for p in patterns if p.strip()]

        print(f"Loaded {len(patterns)} pattern(s) from {lic_path}")
        for idx, pattern in enumerate(patterns, 1):
            preview = pattern[:50].replace("\n", "\\n")
            if len(pattern) > 50:
                preview += "..."
            print(f"  Pattern {idx}: {preview}")

        return patterns

    except Exception as e:
        print(f"Error loading patterns from {lic_path}: {e}")
        return []


def escape_for_regex(text: str) -> str:
    """Escape special regex characters but preserve newlines."""
    # Escape all special regex characters
    escaped = re.escape(text)
    # Unescape newlines so they match actual newlines
    return escaped.replace(r"\n", r"\s*\n\s*")  # Allow whitespace around newlines


def remove_patterns_from_content(content: str, patterns: list[str]) -> str:
    """Remove all patterns from content."""
    cleaned = content

    for pattern in patterns:
        # Escape the pattern for regex matching
        regex_pattern = escape_for_regex(pattern)

        # Try to remove the pattern (case-insensitive, multiline)
        cleaned = re.sub(regex_pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

    return cleaned


def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed."""
    # Skip binary files
    if file_path.suffix.lower() in EXCLUDE_EXTS:
        return False
    if file_path.suffix.lower() in TXT_EXT:
        return True

    if file_path.name.startswith("."):
        return False
    if is_binary(file_path):
        return False
    else:
        return True


def clean_file_worker(args: tuple) -> tuple:
    """Worker function to clean a single file."""
    file_path, patterns = args

    try:
        # Read the file
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            original_content = f.read()

        # Remove patterns
        cleaned_content = remove_patterns_from_content(original_content, patterns)

        # Only write if content changed
        if cleaned_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(cleaned_content)

            removed_chars = len(original_content) - len(cleaned_content)
            return (file_path, True, f"removed {removed_chars} characters")
        else:
            return (file_path, True, "no changes")

    except Exception as e:
        return (file_path, False, str(e))


def main():
    # Load patterns from license file
    if not LIC_FILE.exists():
        print(f"Error: License file not found: {LIC_FILE}")
        return

    patterns = load_patterns(LIC_FILE)

    if not patterns:
        print("No patterns found. Exiting.")
        return

    print()

    # Find all text files recursively
    cwd = Path.cwd()
    all_files = [f for f in cwd.rglob("*") if f.is_file() and should_process_file(f)]

    if not all_files:
        print("No files to process.")
        return

    print(f"Found {len(all_files)} file(s) to process.")
    print(f"Using {NUM_WORKERS} worker(s).\n")
    print("Processing...\n")

    # Prepare arguments for workers
    worker_args = [(file_path, patterns) for file_path in all_files]

    # Process files in parallel
    with Pool(processes=NUM_WORKERS) as pool:
        results = pool.map(clean_file_worker, worker_args)

    # Print results
    success_count = 0
    modified_count = 0
    error_count = 0

    for file_path, success, message in results:
        if success:
            if "no changes" not in message:
                print(f"✓ Modified: {file_path} ({message})")
                modified_count += 1
            else:
                print(f"○ Unchanged: {file_path}")
            success_count += 1
        else:
            print(f"✗ Error: {file_path} - {message}")
            error_count += 1

    print("\nDone.")
    print(f"  Processed: {success_count}/{len(all_files)} file(s)")
    print(f"  Modified: {modified_count} file(s)")
    if error_count > 0:
        print(f"  Failed: {error_count} file(s)")


if __name__ == "__main__":
    main()

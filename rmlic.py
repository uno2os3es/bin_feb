#!/data/data/com.termux/files/usr/bin/env python3
from multiprocessing import Pool, cpu_count
from pathlib import Path

import regex as re
from dh import BIN_EXT, TXT_EXT, is_binary

# -------- CONFIG --------
LIC_FILE = Path("/sdcard/lic")
MIN_BLANK_LINES = 3
NUM_WORKERS = max(cpu_count(), 8)
EXCLUDE_EXTS = BIN_EXT


def load_patterns(lic_path: Path) -> list[str]:
    """Load multiline patterns from the license file."""
    try:
        with open(lic_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        pattern_separator = r"\n(?:\s*\n){" + str(MIN_BLANK_LINES) + r",}"
        patterns = re.split(pattern_separator, content)

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
    escaped = re.escape(text)
    return escaped.replace(r"\n", r"\s*\n\s*")


def remove_patterns_from_content(content: str, patterns: list[str]) -> str:
    """Remove all patterns from content."""
    cleaned = content

    for pattern in patterns:
        regex_pattern = escape_for_regex(pattern)

        cleaned = re.sub(regex_pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

    return cleaned


def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed."""
    if file_path.suffix.lower() in EXCLUDE_EXTS:
        return False
    if file_path.suffix.lower() in TXT_EXT:
        return True

    if file_path.name.startswith("."):
        return False
    return not is_binary(file_path)


def clean_file_worker(args: tuple) -> tuple:
    """Worker function to clean a single file."""
    file_path, patterns = args

    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            original_content = f.read()

        cleaned_content = remove_patterns_from_content(original_content, patterns)

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
    if not LIC_FILE.exists():
        print(f"Error: License file not found: {LIC_FILE}")
        return

    patterns = load_patterns(LIC_FILE)

    if not patterns:
        print("No patterns found. Exiting.")
        return

    print()

    cwd = Path.cwd()
    all_files = [f for f in cwd.rglob("*") if f.is_file() and should_process_file(f)]

    if not all_files:
        print("No files to process.")
        return

    print(f"Found {len(all_files)} file(s) to process.")
    print(f"Using {NUM_WORKERS} worker(s).\n")
    print("Processing...\n")

    worker_args = [(file_path, patterns) for file_path in all_files]

    with Pool(processes=NUM_WORKERS) as pool:
        results = pool.map(clean_file_worker, worker_args)

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

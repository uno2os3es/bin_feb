#!/usr/bin/env python3
import pycld2
from pathlib import Path
from collections import Counter, defaultdict
import sys
import os
from typing import Dict, List, Tuple, Optional
from dh import TXT_EXT

MIN_TEXT_LENGTH = 20

SUPPORTED_EXTENSIONS = TXT_EXT
ENGLISH_LANGUAGES = {"en", "en_US", "en_GB"}
MAX_FILE_SIZE = 1024 * 1024  # 1MB


def detect_language(text: str) -> Tuple[Optional[str], float]:
    """
    Detect language of text using pycld2.
    Returns (language_code, confidence) or (None, 0) if detection fails.
    """
    if not text or len(text) < MIN_TEXT_LENGTH:
        return None, 0

    try:
        # isReliable, textBytesFound, details = pycld2.detect(text)
        reliable, _, details = pycld2.detect(text)
        if reliable and details:
            # details is a list of tuples: (lang_code, lang_name, percent, score)
            # Get the primary language (first result)
            primary_lang = details[0][0]  # Language code
            confidence = details[0][2]  # Percentage confidence
            return primary_lang, confidence
    except Exception as e:
        # pycld2 can throw errors on very short text or special characters
        pass

    return None, 0


def is_likely_english(text: str, threshold: float = 70.0) -> bool:
    """Check if text is likely English based on confidence threshold."""
    lang, confidence = detect_language(text)
    if lang is None:
        return False
    return lang in ENGLISH_LANGUAGES and confidence >= threshold


def read_file_safely(filepath: Path) -> Optional[str]:
    """Read file content safely, handling encoding issues."""
    try:
        # Try UTF-8 first
        return filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Try common encodings
        for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
            try:
                return filepath.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
    except Exception:
        pass
    return None


def get_file_sample(text: str, max_lines: int = 50, max_chars: int = 5000) -> str:
    """
    Get a representative sample of text for language detection.
    Takes first max_lines lines up to max_chars characters.
    """
    lines = text.split("\n")[:max_lines]
    sample = "\n".join(lines)
    if len(sample) > max_chars:
        sample = sample[:max_chars]
    return sample


def analyze_directory(directory: str = ".", show_all: bool = False) -> Dict:
    """
    Analyze all files in directory recursively for language detection.
    Returns a dictionary with statistics and results.
    """
    directory = Path(directory).resolve()
    print(f"🔍 Scanning directory: {directory}")
    print("=" * 70)

    results = {
        "total_files": 0,
        "checked_files": 0,
        "skipped_small": 0,
        "skipped_binary": 0,
        "skipped_encoding": 0,
        "non_english": defaultdict(list),  # language -> list of files
        "english": [],
        "undetermined": [],
        "language_stats": Counter(),
        "directory_stats": defaultdict(lambda: {"total": 0, "non_english": 0}),
    }

    # Walk through all files
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories (optional)
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"__pycache__", "node_modules"}]

        current_dir = Path(root)
        rel_dir = current_dir.relative_to(directory)

        for file in files:
            filepath = current_dir / file

            # Skip files with unsupported extensions
            if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            # Skip files that are too large
            if filepath.stat().st_size > MAX_FILE_SIZE:
                results["skipped_binary"] += 1
                continue

            results["total_files"] += 1
            results["directory_stats"][str(rel_dir)]["total"] += 1

            # Read file content
            content = read_file_safely(filepath)
            if content is None:
                results["skipped_encoding"] += 1
                continue

            # Get a sample for detection
            sample = get_file_sample(content)

            # Skip if sample is too short
            if len(sample) < MIN_TEXT_LENGTH:
                results["skipped_small"] += 1
                continue

            # Detect language
            lang, confidence = detect_language(sample)

            if lang is None:
                results["undetermined"].append(filepath)
                continue

            results["checked_files"] += 1
            results["language_stats"][lang] += 1

            if lang in ENGLISH_LANGUAGES and confidence >= 70:
                results["english"].append(filepath)
            else:
                results["non_english"][lang].append(filepath)
                results["directory_stats"][str(rel_dir)]["non_english"] += 1

    return results


def print_results(results: Dict, show_files: bool = False):
    """Print formatted results."""
    print("\n" + "=" * 70)
    print("📊 LANGUAGE DETECTION RESULTS")
    print("=" * 70)

    # Summary statistics
    total = results["total_files"]
    checked = results["checked_files"]
    non_english_total = sum(len(files) for files in results["non_english"].values())
    english_total = len(results["english"])
    undetermined = len(results["undetermined"])

    print(f"\n📁 Files scanned: {total}")
    print(f"   ├─ Successfully analyzed: {checked} ({checked / total * 100:.1f}%)")
    print(f"   ├─ Skipped (too small): {results['skipped_small']}")
    print(f"   ├─ Skipped (binary/large): {results['skipped_binary']}")
    print(f"   └─ Skipped (encoding issues): {results['skipped_encoding']}")

    print(f"\n🌍 Language breakdown:")
    print(f"   ├─ 🇺🇸 English files: {english_total}")
    for lang, files in sorted(results["non_english"].items(), key=lambda x: len(x[1]), reverse=True):
        percentage = len(files) / checked * 100 if checked > 0 else 0
        print(f"   ├─ 🌐 {lang.upper()}: {len(files)} files ({percentage:.1f}%)")

    if undetermined > 0:
        print(f"   └─ ❓ Undetermined: {undetermined}")

    # Directory statistics (directories with most non-English files)
    if results["directory_stats"]:
        print(f"\n📂 Directories with most non-English files:")

        # Filter directories with at least one non-English file
        dirs_with_non_english = [
            (dir_path, stats) for dir_path, stats in results["directory_stats"].items() if stats["non_english"] > 0
        ]

        # Sort by non-English count
        dirs_with_non_english.sort(key=lambda x: x[1]["non_english"], reverse=True)

        for dir_path, stats in dirs_with_non_english[:10]:  # Show top 10
            percentage = stats["non_english"] / stats["total"] * 100
            print(f"   ├─ {dir_path if dir_path != '.' else '(root)'}:")
            print(f"   │   {stats['non_english']}/{stats['total']} files ({percentage:.1f}% non-English)")

    # List non-English files by language (if requested)
    if show_files and results["non_english"]:
        print(f"\n📄 Non-English files by language:")
        for lang, files in sorted(results["non_english"].items()):
            if files:
                print(f"\n   🌐 {lang.upper()} ({len(files)} files):")
                for filepath in files[:20]:  # Limit to 20 per language
                    rel_path = filepath.relative_to(Path.cwd()) if filepath.is_absolute() else filepath
                    print(f"      └─ {rel_path}")
                if len(files) > 20:
                    print(f"      └─ ... and {len(files) - 20} more")

    # Summary recommendation
    print("\n" + "=" * 70)
    print("🎯 RECOMMENDATION")
    print("=" * 70)

    if non_english_total == 0:
        print("✅ All files appear to be in English! No translation needed.")
    else:
        print(f"📢 Found {non_english_total} non-English files that may need translation.")

        # Suggest directories to translate
        dirs_to_translate = [
            (dir_path, stats) for dir_path, stats in results["directory_stats"].items() if stats["non_english"] > 0
        ]

        if dirs_to_translate:
            print("\n📌 Directories to translate (by priority):")
            for dir_path, stats in sorted(dirs_to_translate, key=lambda x: x[1]["non_english"], reverse=True):
                print(f"   └─ {dir_path if dir_path != '.' else 'current directory'}:")
                print(f"       {stats['non_english']} non-English files to translate")

    print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Find non-English files in directory recursively using pycld2")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to scan (default: current directory)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed file listing")
    parser.add_argument(
        "-l", "--list-languages", action="store_true", help="List all detected languages and their counts"
    )

    args = parser.parse_args()

    try:
        results = analyze_directory(args.directory)
        print_results(results, show_files=args.verbose or args.list_languages)
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

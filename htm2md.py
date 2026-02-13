#!/usr/bin/env python3
"""
Python wrapper for html2md executable to convert HTML files to Markdown.
Supports single file processing and recursive directory processing with multiprocessing.
"""

import argparse
import subprocess
import sys
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Optional


def convert_html_to_md(html_file: Path,
                       executable: str = "html2md") -> tuple[Path, bool]:
    """
    Convert a single HTML file to Markdown using html2md executable.

    Args:
        html_file: Path to the HTML file
        executable: Name or path of the html2md executable

    Returns:
        Tuple of (output_file_path, success_status)
    """
    # Generate output filename by replacing .html with .md
    if html_file.suffix.lower() in [".html", ".htm"]:
        md_file = html_file.with_suffix(".md")
    else:
        print(
            f"Warning: {html_file} doesn't have .html/.htm extension, skipping."
        )
        return (html_file, False)

    try:
        # Run html2md and capture stdout
        result = subprocess.run([executable, str(html_file)],
                                capture_output=True,
                                text=True,
                                check=True)

        # Write stdout to .md file
        md_file.write_text(result.stdout, encoding="utf-8")
        print(f"✓ Converted: {html_file} -> {md_file}")
        return (md_file, True)

    except subprocess.CalledProcessError as e:
        print(f"✗ Error converting {html_file}: {e.stderr}", file=sys.stderr)
        return (html_file, False)
    except FileNotFoundError:
        print(
            f"✗ Error: '{executable}' executable not found. Make sure it's in your PATH.",
            file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error converting {html_file}: {e}",
              file=sys.stderr)
        return (html_file, False)


def find_html_files(directory: Path, recursive: bool = True) -> list[Path]:
    """
    Find all HTML files in a directory.

    Args:
        directory: Directory to search
        recursive: Whether to search recursively

    Returns:
        List of HTML file paths
    """
    if recursive:
        # Use rglob for recursive search
        html_files = list(directory.rglob("*.html")) + list(
            directory.rglob("*.htm"))
    else:
        # Use glob for non-recursive search
        html_files = list(directory.glob("*.html")) + list(
            directory.glob("*.htm"))

    return sorted(html_files)


def process_file_wrapper(args: tuple) -> tuple[Path, bool]:
    """Wrapper function for multiprocessing to unpack arguments."""
    html_file, executable = args
    return convert_html_to_md(html_file, executable)


def main():
    parser = argparse.ArgumentParser(
        description="Convert HTML files to Markdown using html2md executable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Process all HTML files in current directory recursively
  %(prog)s -r                       # Same as above (explicit recursive flag)
  %(prog)s file.html                # Process single file
  %(prog)s /path/to/directory       # Process directory recursively
  %(prog)s /path/to/dir --no-recursive  # Process directory non-recursively
        """,
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="HTML file or directory to process (default: current directory)")

    parser.add_argument("-r",
                        "--recursive",
                        action="store_true",
                        default=True,
                        help="Process directories recursively (default: True)")

    parser.add_argument("--no-recursive",
                        action="store_false",
                        dest="recursive",
                        help="Disable recursive processing")

    parser.add_argument("--executable",
                        default="html2md",
                        help="Path to html2md executable (default: html2md)")

    parser.add_argument(
        "--workers",
        type=int,
        default=cpu_count(),
        help=f"Number of worker processes (default: {cpu_count()})")

    args = parser.parse_args()

    # Convert path to Path object
    input_path = Path(args.path).resolve()

    # Check if path exists
    if not input_path.exists():
        print(f"Error: Path '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Determine files to process
    if input_path.is_file():
        # Single file mode
        html_files = [input_path]
    elif input_path.is_dir():
        # Directory mode
        html_files = find_html_files(input_path, args.recursive)
        if not html_files:
            print(f"No HTML files found in {input_path}")
            sys.exit(0)
        print(f"Found {len(html_files)} HTML file(s) to process")
    else:
        print(f"Error: '{input_path}' is neither a file nor a directory.",
              file=sys.stderr)
        sys.exit(1)

    # Process files
    if len(html_files) == 1:
        # Single file - no need for multiprocessing
        convert_html_to_md(html_files[0], args.executable)
    else:
        # Multiple files - use multiprocessing
        print(f"Using {args.workers} worker process(es)")

        # Prepare arguments for multiprocessing
        process_args = [(f, args.executable) for f in html_files]

        # Use multiprocessing Pool
        with Pool(processes=args.workers) as pool:
            results = pool.map(process_file_wrapper, process_args)

        # Summary
        successful = sum(1 for _, success in results if success)
        print(f"\n{'=' * 50}")
        print(
            f"Conversion complete: {successful}/{len(html_files)} files converted successfully"
        )


if __name__ == "__main__":
    main()

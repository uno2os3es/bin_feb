#!/data/data/com.termux/files/usr/bin/env python3
"""
Sort lines in a file and write unique lines back.
Uses mmap for efficient handling of large files.
Reads filename as command-line argument.
"""

import argparse
import mmap
import os
import shutil
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Generator
from datetime import datetime
from pathlib import Path


class LineProcessor:
    """Process lines from files with mmap support."""

    def __init__(self, verbose: bool = False):
        """
        Initialize LineProcessor.

        Args:
            verbose: Print detailed information
        """
        self.verbose = verbose

    def log(self, message: str):
        """Log message if verbose."""
        if self.verbose:
            print(f"[INFO] {message}")

    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        return file_path.stat().st_size

    def format_size(self, size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


class MmapReader(LineProcessor):
    """Read lines from file using mmap."""

    def __init__(self, verbose: bool = False):
        """Initialize MmapReader."""
        super().__init__(verbose=verbose)

    def read_lines_mmap(
        self, file_path: Path, encoding: str = "utf-8", skip_empty: bool = False
    ) -> Generator[str, None, None]:
        """
        Read lines from file using mmap.

        Args:
            file_path: Path to file
            encoding: File encoding
            skip_empty: Skip empty lines

        Yields:
            Lines from file
        """
        file_size = self.get_file_size(file_path)
        self.log(f"Reading {file_path} ({self.format_size(file_size)})")

        try:
            with open(file_path, "rb") as f:
                if file_size > 1024 * 1024:
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                        offset = 0
                        while offset < len(mmapped_file):
                            newline_pos = mmapped_file.find(b"\n", offset)

                            if newline_pos == -1:
                                line_bytes = mmapped_file[offset:]
                            else:
                                line_bytes = mmapped_file[offset:newline_pos]

                            try:
                                line = line_bytes.decode(encoding).rstrip("\r\n")

                                if not skip_empty or line.strip():
                                    yield line

                            except UnicodeDecodeError as e:
                                self.log(f"Warning: Encoding error at offset {offset}: {e!s}")

                            offset = newline_pos + 1

                            if newline_pos == -1:
                                break

                else:
                    f.seek(0)
                    for line in f:
                        decoded_line = line.rstrip("\r\n")

                        if not skip_empty or decoded_line.strip():
                            yield decoded_line

        except Exception as e:
            raise OSError(f"Error reading file: {e!s}")

    def read_lines_regular(
        self, file_path: Path, encoding: str = "utf-8", skip_empty: bool = False
    ) -> Generator[str, None, None]:
        """
        Read lines using regular file operations.

        Args:
            file_path: Path to file
            encoding: File encoding
            skip_empty: Skip empty lines

        Yields:
            Lines from file
        """
        self.log(f"Reading {file_path} (regular mode)")

        try:
            with open(file_path, encoding=encoding) as f:
                for line in f:
                    decoded_line = line.rstrip("\r\n")

                    if not skip_empty or decoded_line.strip():
                        yield decoded_line

        except Exception as e:
            raise OSError(f"Error reading file: {e!s}")

    def read_lines(
        self, file_path: Path, encoding: str = "utf-8", skip_empty: bool = False, use_mmap: bool = True
    ) -> Generator[str, None, None]:
        """
        Read lines from file (auto-selects best method).

        Args:
            file_path: Path to file
            encoding: File encoding
            skip_empty: Skip empty lines
            use_mmap: Use mmap for large files

        Yields:
            Lines from file
        """
        if use_mmap:
            yield from self.read_lines_mmap(file_path, encoding, skip_empty)
        else:
            yield from self.read_lines_regular(file_path, encoding, skip_empty)


class LineSorter(LineProcessor):
    """Sort lines with various methods."""

    def __init__(self, verbose: bool = False):
        """Initialize LineSorter."""
        super().__init__(verbose=verbose)

    def sort_in_memory(self, lines: list[str], reverse: bool = False, case_insensitive: bool = False) -> list[str]:
        """
        Sort lines in memory.

        Args:
            lines: List of lines
            reverse: Sort in reverse order
            case_insensitive: Case-insensitive sorting

        Returns:
            Sorted list of lines
        """
        self.log(f"Sorting {len(lines)} lines in memory")

        if case_insensitive:
            return sorted(lines, key=str.lower, reverse=reverse)
        else:
            return sorted(lines, reverse=reverse)

    def sort_with_temp_files(
        self,
        file_path: Path,
        chunk_size: int = 100000,
        reverse: bool = False,
        encoding: str = "utf-8",
        case_insensitive: bool = False,
    ) -> list[Path]:
        """
        Sort large file using temporary files (external sorting).

        Args:
            file_path: Path to file
            chunk_size: Lines per chunk
            reverse: Sort in reverse order
            encoding: File encoding
            case_insensitive: Case-insensitive sorting

        Returns:
            List of sorted temp file paths
        """
        self.log(f"Sorting large file using external sorting (chunk size: {chunk_size})")

        reader = MmapReader(verbose=self.verbose)
        temp_files = []

        try:
            chunk = []
            temp_dir = Path(tempfile.gettempdir())

            for _i, line in enumerate(reader.read_lines(file_path, encoding)):
                chunk.append(line)

                if len(chunk) >= chunk_size:
                    sorted_chunk = self.sort_in_memory(chunk, reverse, case_insensitive)

                    temp_file = temp_dir / f".sort_chunk_{os.getpid()}_{len(temp_files)}.tmp"
                    with open(temp_file, "w", encoding=encoding) as f:
                        for line in sorted_chunk:
                            f.write(line + "\n")

                    temp_files.append(temp_file)
                    chunk = []

                    self.log(f"Written {len(temp_files)} chunk(s)")

            if chunk:
                sorted_chunk = self.sort_in_memory(chunk, reverse, case_insensitive)

                temp_file = temp_dir / f".sort_chunk_{os.getpid()}_{len(temp_files)}.tmp"
                with open(temp_file, "w", encoding=encoding) as f:
                    for line in sorted_chunk:
                        f.write(line + "\n")

                temp_files.append(temp_file)

            return temp_files

        except Exception:
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
            raise


class LineDeduplicator(LineProcessor):
    """Deduplicate lines."""

    def __init__(self, verbose: bool = False):
        """Initialize LineDeduplicator."""
        super().__init__(verbose=verbose)

    def deduplicate_list(self, lines: list[str], preserve_order: bool = False) -> list[str]:
        """
        Deduplicate lines.

        Args:
            lines: List of lines
            preserve_order: Preserve original order

        Returns:
            Deduplicated list
        """
        if preserve_order:
            self.log(f"Deduplicating {len(lines)} lines (preserving order)")
            seen = set()
            unique = []

            for line in lines:
                if line not in seen:
                    seen.add(line)
                    unique.append(line)

            return unique

        else:
            self.log(f"Deduplicating {len(lines)} lines")
            return list(dict.fromkeys(lines))

    def deduplicate_generator(self, lines: Generator[str, None, None]) -> Generator[str, None, None]:
        """
        Deduplicate lines from generator (low memory).

        Args:
            lines: Generator of lines

        Yields:
            Unique lines
        """
        seen = set()
        count = 0

        for line in lines:
            if line not in seen:
                seen.add(line)
                yield line
                count += 1

        self.log(f"Found {count} unique lines")


class FileSorter(LineProcessor):
    """Main file sorting and deduplication engine."""

    def __init__(self, verbose: bool = False, dry_run: bool = False):
        """
        Initialize FileSorter.

        Args:
            verbose: Verbose output
            dry_run: Don't modify files
        """
        super().__init__(verbose=verbose)
        self.dry_run = dry_run
        self.reader = MmapReader(verbose=verbose)
        self.sorter = LineSorter(verbose=verbose)
        self.deduplicator = LineDeduplicator(verbose=verbose)

    def process_file(
        self,
        file_path: str,
        output_path: str | None = None,
        sort: bool = True,
        unique: bool = True,
        reverse: bool = False,
        case_insensitive: bool = False,
        skip_empty: bool = False,
        backup: bool = True,
        encoding: str = "utf-8",
    ) -> dict:
        """
        Process file: sort and/or deduplicate lines.

        Args:
            file_path: Path to input file
            output_path: Path to output file (default: overwrite input)
            sort: Sort lines
            unique: Remove duplicates
            reverse: Sort in reverse order
            case_insensitive: Case-insensitive sorting
            skip_empty: Skip empty lines
            backup: Create backup of original file
            encoding: File encoding

        Returns:
            Dictionary with processing statistics
        """
        input_path = Path(file_path)

        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if output_path is None:
            output_path = file_path

        output_path = Path(output_path)

        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║              File Line Sorter & Deduplicator               ║")
        print("╚════════════════════════════════════════════════════════════╝\n")

        print(f"Input file: {input_path}")
        print(f"Output file: {output_path}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'NORMAL'}")
        print("-" * 60)

        start_time = time.time()

        try:
            original_size = self.get_file_size(input_path)
            original_lines = sum(1 for _ in self.reader.read_lines(input_path, encoding, skip_empty))

            self.log(f"Original file: {original_lines} lines, {self.format_size(original_size)}")

            lines = list(self.reader.read_lines(input_path, encoding, skip_empty))

            if sort:
                lines = self.sorter.sort_in_memory(lines, reverse, case_insensitive)
                self.log("Lines sorted")

            unique_count = len(lines)
            if unique:
                lines = self.deduplicator.deduplicate_list(lines, preserve_order=not sort)
                unique_count = original_lines - len(lines)
                self.log(f"Removed {unique_count} duplicate lines")

            if not self.dry_run:
                if backup and output_path == input_path:
                    backup_path = input_path.with_suffix(input_path.suffix + ".bak")
                    shutil.copy2(input_path, backup_path)
                    self.log(f"Backup created: {backup_path}")

                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding=encoding) as f:
                    for line in lines:
                        f.write(line + "\n")

                self.log(f"Output written: {output_path}")

            else:
                self.log("DRY RUN: File not written")

            if not self.dry_run:
                final_size = self.get_file_size(output_path)
            else:
                final_size = sum(len(line.encode(encoding)) + 1 for line in lines)

            elapsed_time = time.time() - start_time

            return {
                "input_file": str(input_path),
                "output_file": str(output_path),
                "original_lines": original_lines,
                "original_size_bytes": original_size,
                "original_size": self.format_size(original_size),
                "final_lines": len(lines),
                "final_size_bytes": final_size,
                "final_size": self.format_size(final_size),
                "duplicate_lines": unique_count if unique else 0,
                "size_reduction": original_size - final_size if original_size > 0 else 0,
                "size_reduction_pct": ((original_size - final_size) / original_size * 100) if original_size > 0 else 0,
                "processing_time": elapsed_time,
                "lines_per_second": original_lines / elapsed_time if elapsed_time > 0 else 0,
            }

        except Exception as e:
            raise RuntimeError(f"Error processing file: {e!s}")

    def print_stats(self, stats: dict):
        """Print statistics."""
        print("\n" + "=" * 60)
        print("STATISTICS")
        print("=" * 60)
        print(f"Original lines: {stats['original_lines']:,}")
        print(f"Final lines: {stats['final_lines']:,}")

        if stats["duplicate_lines"] > 0:
            dup_pct = (stats["duplicate_lines"] / stats["original_lines"] * 100) if stats["original_lines"] > 0 else 0
            print(f"Duplicate lines removed: {stats['duplicate_lines']:,} ({dup_pct:.1f}%)")

        print()
        print(f"Original size: {stats['original_size']}")
        print(f"Final size: {stats['final_size']}")

        if stats["size_reduction"] > 0:
            print(f"Size reduction: {self.format_size(stats['size_reduction'])} ({stats['size_reduction_pct']:.1f}%)")

        print()
        print(f"Processing time: {stats['processing_time']:.2f} seconds")
        print(f"Speed: {stats['lines_per_second']:,.0f} lines/second")
        print("=" * 60)

    def save_report(self, stats: dict, report_file: str | None = None):
        """Save statistics report."""
        if report_file is None:
            report_file = "sort_unique_report.json"

        import json

        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
        }

        try:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n✓ Report saved: {report_file}")
        except Exception as e:
            print(f"\n✗ Error saving report: {e!s}")


class FileAnalyzer(LineProcessor):
    """Analyze file before processing."""

    def __init__(self, verbose: bool = False):
        """Initialize FileAnalyzer."""
        super().__init__(verbose=verbose)
        self.reader = MmapReader(verbose=verbose)

    def analyze_file(self, file_path: Path, encoding: str = "utf-8") -> dict:
        """
        Analyze file statistics.

        Args:
            file_path: Path to file
            encoding: File encoding

        Returns:
            Analysis dictionary
        """
        file_size = self.get_file_size(file_path)
        lines = list(self.reader.read_lines(file_path, encoding))

        line_counts = Counter(lines)
        duplicate_count = sum(count - 1 for count in line_counts.values())

        max_length = max((len(line) for line in lines), default=0)
        avg_length = sum(len(line) for line in lines) / len(lines) if lines else 0

        most_common = line_counts.most_common(10)

        return {
            "file": str(file_path),
            "size_bytes": file_size,
            "size": self.format_size(file_size),
            "total_lines": len(lines),
            "unique_lines": len(line_counts),
            "duplicate_lines": duplicate_count,
            "duplicate_percentage": (duplicate_count / len(lines) * 100) if lines else 0,
            "max_line_length": max_length,
            "avg_line_length": avg_length,
            "most_common_lines": most_common,
        }

    def print_analysis(self, file_path: Path, encoding: str = "utf-8"):
        """Print file analysis."""
        analysis = self.analyze_file(file_path, encoding)

        print(f"\n{'=' * 60}")
        print(f"File Analysis: {file_path.name}")
        print(f"{'=' * 60}")

        print("\nBasic Statistics:")
        print(f"  Size: {analysis['size']}")
        print(f"  Total lines: {analysis['total_lines']:,}")
        print(f"  Unique lines: {analysis['unique_lines']:,}")
        print(f"  Duplicate lines: {analysis['duplicate_lines']:,} ({analysis['duplicate_percentage']:.1f}%)")

        print("\nLine Length Statistics:")
        print(f"  Maximum: {analysis['max_line_length']} characters")
        print(f"  Average: {analysis['avg_line_length']:.1f} characters")

        if analysis["most_common_lines"]:
            print("\nMost Common Lines (Top 10):")
            for line, count in analysis["most_common_lines"]:
                display_line = line[:47] + "..." if len(line) > 50 else line
                print(f"  ({count}x) {display_line}")

        print(f"{'=' * 60}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sort lines in a file and remove duplicates (uses mmap for large files)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sort and deduplicate a file
  python sort_unique_lines.py input.txt

  # Sort only (no deduplication)
  python sort_unique_lines.py input.txt --no-unique

  # Deduplicate only (no sorting)
  python sort_unique_lines.py input.txt --no-sort

  # Save to different output file
  python sort_unique_lines.py input.txt --output sorted_output.txt

  # Reverse sort
  python sort_unique_lines.py input.txt --reverse

  # Case-insensitive sorting
  python sort_unique_lines.py input.txt --case-insensitive

  # Skip empty lines
  python sort_unique_lines.py input.txt --skip-empty

  # Dry run (preview)
  python sort_unique_lines.py input.txt --dry-run -v

  # Analyze file before processing
  python sort_unique_lines.py input.txt --analyze

  # With report
  python sort_unique_lines.py input.txt --report stats.json

  # Verbose output
  python sort_unique_lines.py input.txt -v
        """,
    )

    parser.add_argument("filename", help="Input filename")
    parser.add_argument("--output", "-o", help="Output filename (default: overwrite input)")
    parser.add_argument("--sort", action="store_true", default=True, help="Sort lines (default: True)")
    parser.add_argument("--no-sort", dest="sort", action="store_false", help="Do not sort lines")
    parser.add_argument("--unique", action="store_true", default=True, help="Remove duplicates (default: True)")
    parser.add_argument("--no-unique", dest="unique", action="store_false", help="Do not remove duplicates")
    parser.add_argument("--reverse", "-r", action="store_true", help="Sort in reverse order")
    parser.add_argument("--case-insensitive", "-i", action="store_true", help="Case-insensitive sorting")
    parser.add_argument("--skip-empty", action="store_true", help="Skip empty lines")
    parser.add_argument("--no-backup", action="store_true", help="Do not create backup file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without modifying files")
    parser.add_argument("--analyze", action="store_true", help="Analyze file before processing")
    parser.add_argument("--report", "-R", metavar="FILE", help="Save report to JSON file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8)")

    args = parser.parse_args()

    try:
        input_path = Path(args.filename)

        if not input_path.exists():
            print(f"Error: File not found: {args.filename}")
            sys.exit(1)

        if args.analyze:
            analyzer = FileAnalyzer(verbose=args.verbose)
            analyzer.print_analysis(input_path, args.encoding)
            return

        sorter = FileSorter(verbose=args.verbose, dry_run=args.dry_run)

        stats = sorter.process_file(
            args.filename,
            output_path=args.output,
            sort=args.sort,
            unique=args.unique,
            reverse=args.reverse,
            case_insensitive=args.case_insensitive,
            skip_empty=args.skip_empty,
            backup=not args.no_backup,
            encoding=args.encoding,
        )

        sorter.print_stats(stats)

        if args.report:
            sorter.save_report(stats, args.report)

    except Exception as e:
        print(f"Error: {e!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/env python3
# ripgrep_py.py
# Minimal ripgrep-like recursive search tool in Python.

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import fnmatch
import os
import stat
import sys
from typing import TYPE_CHECKING

from dh import is_binary_file
import regex as re

if TYPE_CHECKING:
    from collections.abc import Iterable

# ========= Configuration (tweak as desired) =========
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
}
BINARY_CHUNK = 4096
DEFAULT_THREADS = max(4, (os.cpu_count() or 4))
# ====================================================

# ---------- Utility: terminal color ----------
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"
ANSI_HIGHLIGHT = "\033[31m"  # red; allow environment/no-color override


def colorize(
    text: str,
    start: int,
    end: int,
    enable: bool = True,
) -> str:
    if not enable:
        return text
    return text[:start] + ANSI_HIGHLIGHT + ANSI_BOLD + text[start:end] + ANSI_RESET + text[end:]


# ---------- File matching for include/exclude globs ----------


def matches_any_glob(path: str, patterns: Iterable[str]) -> bool:
    basename = os.path.basename(path)
    return any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch(basename, p) for p in patterns)


# ---------- Collect candidate files ----------


def collect_files(
    roots: Iterable[str],
    include_hidden: bool = False,
    include_globs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    follow_symlinks: bool = False,
    max_filesize: int | None = None,
) -> Iterable[str]:
    include_globs = include_globs or []
    exclude_globs = exclude_globs or []

    for root in roots:
        if os.path.isfile(root):
            yield root
            continue
        for (
            dirpath,
            dirnames,
            filenames,
        ) in os.walk(root, followlinks=follow_symlinks):
            # prune ignored dirs and hidden dirs if needed
            dirnames[:] = [
                d
                for d in dirnames
                if (include_hidden or not d.startswith("."))
                and d not in IGNORED_DIRS
                and not matches_any_glob(
                    os.path.join(dirpath, d),
                    exclude_globs,
                )
            ]
            for fn in filenames:
                if not include_hidden and fn.startswith("."):
                    continue
                full = os.path.join(dirpath, fn)
                if matches_any_glob(full, exclude_globs):
                    continue
                if include_globs and not matches_any_glob(full, include_globs):
                    continue
                try:
                    st = os.stat(full)
                    if not stat.S_ISREG(st.st_mode):
                        continue
                    if max_filesize and st.st_size > max_filesize:
                        continue
                except Exception:
                    continue
                yield full


# ---------- Search single file ----------


def search_file_text_mode(
    path: str,
    regex: re.Pattern | None,
    fixed: str | None,
    ignore_case: bool,
    show_line_numbers: bool,
    color: bool,
    max_matches: int | None = None,
) -> tuple[
    str,
    list[tuple[int, str, list[tuple[int, int]]]],
]:
    """Returns: (path, [ (lineno, line_text, [ (match_start, match_end), ...] ), ... ])."""
    matches = []
    try:
        with open(
            path,
            encoding="utf-8",
            errors="replace",
        ) as fh:
            for lineno, raw_line in enumerate(fh, start=1):
                line = raw_line.rstrip("\n")
                spans: list[tuple[int, int]] = []
                if regex:
                    for m in regex.finditer(line):
                        spans.append((m.start(), m.end()))
                else:
                    # fixed-string search (possibly case-insensitive)
                    hay = line.lower() if ignore_case else line
                    needle = fixed.lower() if ignore_case else fixed
                    start = 0
                    while True:
                        idx = hay.find(needle, start)
                        if idx == -1:
                            break
                        spans.append(
                            (
                                idx,
                                idx + len(needle),
                            )
                        )
                        start = idx + max(1, len(needle))
                if spans:
                    matches.append((lineno, line, spans))
                    if max_matches and len(matches) >= max_matches:
                        break
    except Exception:
        # cannot read file — return empty
        return path, []
    return path, matches


# ---------- Main CLI ----------


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ripgrep-like recursive search in Python")
    p.add_argument(
        "pattern",
        nargs="?",
        help="Regex pattern (positional) or use -e",
    )
    p.add_argument(
        "-e",
        "--regexp",
        dest="pattern_e",
        help="Pattern (alternative to positional)",
    )
    p.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="Case-insensitive search",
    )
    p.add_argument(
        "-F",
        "--fixed-strings",
        action="store_true",
        help="Fixed string search (no regex)",
    )
    p.add_argument(
        "-n",
        "--line-number",
        action="store_true",
        help="Show line numbers",
    )
    p.add_argument(
        "-l",
        "--files-with-matches",
        action="store_true",
        help="Only print filenames that match",
    )
    p.add_argument(
        "-c",
        "--count",
        action="store_true",
        help="Print count of matches per file",
    )
    p.add_argument(
        "-t",
        "--threads",
        type=int,
        default=DEFAULT_THREADS,
        help="Number of worker threads",
    )
    p.add_argument(
        "--hidden",
        action="store_true",
        help="Search hidden files and directories",
    )
    p.add_argument(
        "--glob",
        action="append",
        help="Include glob (fnmatch); can be repeated",
    )
    p.add_argument(
        "--exclude",
        action="append",
        help="Exclude glob (fnmatch); can be repeated",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colorized output",
    )
    p.add_argument(
        "--max-filesize",
        type=int,
        default=10_000_000,
        help="Skip files larger than size (bytes)",
    )
    p.add_argument(
        "--follow",
        action="store_true",
        help="Follow symlinks",
    )
    p.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to search (default: .)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)
    pattern = args.pattern_e or args.pattern
    if not pattern:
        print(
            "No pattern provided. Use positional PATTERN or -e PATTERN.",
            file=sys.stderr,
        )
        return 2

    ignore_case = args.ignore_case
    fixed = args.fixed_strings
    compiled = None
    if not fixed:
        flags = re.MULTILINE
        if ignore_case:
            flags |= re.IGNORECASE
        try:
            compiled = re.compile(pattern, flags)
        except re.error as ex:
            print(
                f"Invalid regex: {ex}",
                file=sys.stderr,
            )
            return 2

    include_globs = args.glob or []
    exclude_globs = args.exclude or []

    # gather candidate files
    candidates = list(
        collect_files(
            args.paths,
            include_hidden=args.hidden,
            include_globs=include_globs,
            exclude_globs=exclude_globs,
            follow_symlinks=args.follow,
            max_filesize=args.max_filesize,
        )
    )

    if not candidates:
        return 0

    color = not args.no_color and sys.stdout.isatty()
    any_match = False
    results_per_file = {}

    # Worker: skip binary files quickly, then search
    def worker(path: str):
        if is_binary_file(path):
            return path, []
        return search_file_text_mode(
            path,
            regex=compiled,
            fixed=pattern if fixed else None,
            ignore_case=ignore_case,
            show_line_numbers=args.line_number,
            color=color,
        )

    # Use ThreadPoolExecutor for concurrent IO-bound file reads
    with ThreadPoolExecutor(max_workers=args.threads) as ex:
        futures = {ex.submit(worker, p): p for p in candidates}
        try:
            for fut in as_completed(futures):
                path, matches = fut.result()
                if not matches:
                    continue
                any_match = True  # mutating outer var; final return depends on this
                results_per_file[path] = matches
                # Output streaming: if files-with-matches, print filename and continue
                if args.files_with_matches:
                    print(path)
                    # avoid printing repeats
                elif args.count:
                    print(f"{path}:{len(matches)}")
                else:
                    for (
                        lineno,
                        line,
                        spans,
                    ) in matches:
                        # build highlighted line
                        out_line = line
                        if color and spans:
                            # apply highlights from end -> start to not shift indices
                            for s, e in sorted(
                                spans,
                                key=lambda x: x[0],
                                reverse=True,
                            ):
                                out_line = colorize(
                                    out_line,
                                    s,
                                    e,
                                    enable=True,
                                )
                        if args.line_number:
                            print(f"{path}:{lineno}:{out_line}")
                        else:
                            print(f"{path}:{out_line}")
        except KeyboardInterrupt:
            print(
                "\nSearch cancelled.",
                file=sys.stderr,
            )
            return 130

    return 0 if any_match else 1


if __name__ == "__main__":
    sys.exit(main())

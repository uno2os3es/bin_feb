#!/data/data/com.termux/files/usr/bin/env python3
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import mmap
import os
import tokenize

import regex as re
from tqdm import tqdm

SIZE_THRESHOLD = 1 * 1024 * 1024
OLD_PRINT_RE = re.compile(r"(?m)^[ \t]*print[ \t]+[^(\n]")


def _open_source(filepath: str):
    size = os.path.getsize(filepath)
    f = open(filepath, "rb")
    if size > SIZE_THRESHOLD:
        return mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    return f


def _read_text(filepath: str) -> str | None:
    try:
        with open(
            filepath,
            encoding="utf-8",
            errors="ignore",
        ) as f:
            return f.read()
    except Exception:
        return None


def _has_rich_print_import(text: str) -> bool:
    return "from rich import print" in text


def regex_flag(filepath: str) -> bool:
    text = _read_text(filepath)
    if not text:
        return False
    if _has_rich_print_import(text):
        return False
    return bool(OLD_PRINT_RE.search(text))


def tokenizer_confirm(
    filepath: str,
) -> str | None:
    try:
        src = _open_source(filepath)
        tokens = list(tokenize.tokenize(src.readline))
    except Exception:
        return None
    for i, tok in enumerate(tokens):
        if tok.type == tokenize.NAME and tok.string == "print":
            line = tok.line.rstrip()
            if line.strip() == "print":
                continue
            j = i + 1
            while j < len(tokens) and tokens[j].type in {
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.INDENT,
                tokenize.DEDENT,
            }:
                j += 1
            if j < len(tokens) and tokens[j].string != "(":
                return line
    return None


def autofix_file(filepath: str) -> bool:
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
        if any(l.strip() == "from rich import print" for l in lines):
            return False
        changed = False
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.rstrip() == "print":
                continue
            if stripped.startswith("print ") and not stripped.startswith("print("):
                indent = line[: len(line) - len(stripped)]
                content = stripped[len("print ") :].rstrip()
                lines[i] = f"{indent}print({content})\n"
                changed = True
        if changed:
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(lines)
        return changed
    except Exception:
        return False


def process_file(filepath: str, autofix: bool) -> tuple[str, str] | None:
    if not regex_flag(filepath):
        return None
    confirmed = tokenizer_confirm(filepath)
    if not confirmed:
        return None
    if autofix:
        autofix_file(filepath)
    return filepath, confirmed


def collect_py_files(root: str) -> list[str]:
    out: list[str] = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(".py"):
                out.append(os.path.join(dirpath, name))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Regex + tokenizer detection of Python 2 print")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("-a", "--autofix", action="store_true")
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=os.cpu_count(),
    )
    args = parser.parse_args()
    py_files = collect_py_files(args.path)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_file, f, args.autofix) for f in py_files]
        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="",
            unit="file",
        ):
            result = future.result()
            if result:
                path, line = result
                print(f"{path}\n  {line}")


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/python
import ast
import io
import shutil
import tempfile
import tokenize
from multiprocessing import Pool
from pathlib import Path

import regex as re
from deep_translator import GoogleTranslator
from fastwalk import walk_files
from tqdm import tqdm

DIRECTORY = "."
non_english_pattern = re.compile(r"[^\x00-\x7F]")


def is_english(text: str) -> bool:
    return not non_english_pattern.search(text)


def chunk_text(text: str, size: int = 800) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


def translate_chunk(chunk: str) -> str:
    try:
        result = GoogleTranslator(source="auto", target="en").translate(chunk)
        return result if result else chunk
    except Exception:
        return chunk


def translate_text(text: str) -> str:
    chunks = chunk_text(text)
    with Pool(8) as pool:
        translated = list(pool.imap(translate_chunk, chunks))
    return "".join(translated)


def safe_overwrite(filepath: Path, content: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=filepath.parent,
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    shutil.move(tmp_path, filepath)


# ---------- PYTHON-SAFE TRANSLATION ----------


def extract_docstrings(
    tree: ast.AST,
) -> dict[int, str]:
    docstrings = {}

    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.Module,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            doc = ast.get_docstring(node, clean=False)
            if doc and not is_english(doc):
                docstrings[id(node)] = doc
    return docstrings


def translate_python_file(source: str) -> str:
    tree = ast.parse(source)
    docstrings = extract_docstrings(tree)
    {k: translate_text(v) for k, v in docstrings.items()}

    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    output = []

    for tok in tokens:
        tok_type, tok_str, *_ = tok

        if tok_type == tokenize.COMMENT and not is_english(tok_str):
            tok_str = translate_text(tok_str)

        elif tok_type == tokenize.STRING:
            stripped = tok_str.strip("'\"")
            if not is_english(stripped):
                try:
                    translated = translate_text(stripped)
                    quote = tok_str[0]
                    tok_str = f"{quote}{translated}{quote}"
                except Exception:
                    pass

        output.append(tok_str)

    return "".join(output)


# ---------- FILE PROCESSING ----------


def process_files(directory: str) -> None:
    paths = [Path(p) for p in walk_files(directory)]
    files = [p for p in paths if p.is_file()]

    for fp in tqdm(files, desc="Scanning files"):
        suffix = fp.suffix.lower()

        if suffix not in {
            ".txt",
            ".md",
            ".srt",
            ".json",
            ".html",
            ".py",
        }:
            continue

        try:
            original = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if is_english(original.strip()):
            continue

        translated = translate_python_file(original) if suffix == ".py" else translate_text(original)

        if translated.strip() == original.strip():
            continue

        safe_overwrite(fp, translated)
        print(f"Translated safely: {fp}")


if __name__ == "__main__":
    process_files(DIRECTORY)

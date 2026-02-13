#!/data/data/com.termux/files/usr/bin/python

import ast
import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import regex as re
from deep_translator import GoogleTranslator

PYTHON_EXT = ".py"
BACKUP_EXT = ".bak"
CHUNK_SIZE = 5000  # chars, for splitting large files
TARGET_LANG = "en"
SRC_LANG = "auto"

# Thread-local storage for the translator to avoid threading issues
_thread_local = threading.local()


def get_size(filepath):
    return Path(filepath).stat().st_size


def get_translator():
    if not hasattr(_thread_local, "translator"):
        _thread_local.translator = GoogleTranslator(
            source=SRC_LANG,
            target=TARGET_LANG,
        )
    return _thread_local.translator


def is_non_english(line):
    # Consider a line non-English if it contains non-ascii and not all in [a-zA-Z0-9]
    return re.search(r"[^\x00-\x7F]", line)


def translate_line(line):
    # Only attempt translation if non-English detected
    if is_non_english(line.strip()):
        try:
            trans = get_translator().translate(line.strip())
            if trans and trans.strip() and trans.strip() != line.strip():
                return trans
        except Exception as e:
            print(f"Translation error: {e} -- Line: {line}")
            return None
    return None


def split_large_text_blocks(text, max_len):
    # Splits text into chunks <=max_len, only at line boundaries
    lines = text.splitlines(keepends=True)
    chunks = []
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) > max_len:
            chunks.append(chunk)
            chunk = ""
        chunk += line
    if chunk:
        chunks.append(chunk)
    return chunks


def translate_docstring(docstr):
    # Insert translation after each non-English line in docstring
    new_lines = []
    for line in docstr.splitlines():
        new_lines.append(line)
        transl = translate_line(line)
        if transl:
            new_lines.append(transl)
    return "\n".join(new_lines)


def process_file(filepath):
    # Backup original
    backup_path = filepath + BACKUP_EXT
    shutil.copyfile(filepath, backup_path)

    with open(filepath, encoding="utf-8") as f:
        code = f.read()

    if len(code) > CHUNK_SIZE:
        # process in chunks, careful not to break syntax (prefer splitting on function/class boundaries)
        # For simplicity, just process as one; for huge files, parsing could be slow
        pass

    # Parse AST to find docstrings (for accuracy)
    try:
        parsed = ast.parse(
            code,
            filename=filepath,
            type_comments=True,
        )
    except Exception as e:
        print(f"Failed to parse {filepath}: {e}")
        return

    lines = code.splitlines(keepends=False)
    new_lines = list(lines)
    offset_map = {}  # original line#: offset from inserted lines

    # Process docstrings
    for node in ast.walk(parsed):
        if isinstance(
                node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Module,
            ),
        ):
            docstring = ast.get_docstring(node, clean=False)
            if docstring:
                doc_start = node.body[0].lineno - 1 if node.body else None
                # Find the line number of the docstring: look for triple quote line
                for lookback in range(3):
                    possible = doc_start - lookback
                    if possible >= 0 and (
                            lines[possible].lstrip().startswith('"""')
                            or lines[possible].lstrip().startswith("'''")):
                        docstring_line = possible
                        break
                else:
                    continue  # couldn't find docstring line, skip

                doc_lines = []
                line_idx = docstring_line
                quote_type = '"""' if lines[line_idx].lstrip().startswith(
                    '"""') else "'''"
                # Accumulate lines until the closing triple-quote
                while True:
                    doc_lines.append(lines[line_idx])
                    if lines[line_idx].rstrip().endswith(
                            quote_type) and line_idx != docstring_line:
                        break
                    line_idx += 1
                doc_block = "\n".join(doc_lines)
                # Extract the content inside the quotes (for docstring only)
                doc_body = re.sub(
                    rf"^{quote_type}|{quote_type}$",
                    "",
                    doc_block.strip(),
                    flags=re.MULTILINE,
                ).strip()
                # Replace only the lines within the docstring that need translation
                translated_doc_body = translate_docstring(doc_body)
                translated_doc_block = f"{quote_type}\n{translated_doc_body}\n{quote_type}"
                # Replace lines in new_lines (accounting for already inserted lines)
                start = docstring_line + offset_map.get(docstring_line, 0)
                end = line_idx + 1 + offset_map.get(line_idx, 0)
                translated_lines = translated_doc_block.splitlines()
                new_lines[start:end] = translated_lines
                # Update offset for subsequent insertions
                offset = len(translated_lines) - (end - start)
                for k in range(end, len(new_lines)):
                    offset_map[k] = offset_map.get(k, 0) + offset

    # Process line comments (# ...)
    final_lines = []
    for line in new_lines:
        final_lines.append(line)
        stripped = line.strip()
        if stripped.startswith("#") and is_non_english(stripped[1:]):
            # Only translate the comment part (after the first #)
            trans = translate_line(stripped[1:].strip())
            if trans:
                # Insert translated comment in next line, keep comment mark
                indentation = re.match(r"\s*", line).group(0)
                final_lines.append(f"{indentation}# {trans}")

    # Save file back
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines) + "\n")

    print(f"Translated: {filepath}")


def find_py_files(root="."):
    files = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(PYTHON_EXT) and get_size(
                    os.path.join(dirpath, fname)) != 0:
                files.append(os.path.join(dirpath, fname))
    return files


def main():
    py_files = find_py_files(".")
    if not py_files:
        print("No Python files found.")
        return

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(process_file, f): f for f in py_files}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Failed processing {futures[future]}: {e}")


if __name__ == "__main__":
    main()

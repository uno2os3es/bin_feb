#!/data/data/com.termux/files/usr/bin/env python3
import os
import shutil
import tarfile
import tempfile
import zipfile

import dh

EXT = {".txt"}
# STRTOFIND = [
# "namespace", '#ifndef', '#ifdef', '#include', '#ifnodef', '#endif',
# '#else', '#if', '// File:'
# ]
STRTOFIND = [
    "import ",
    "__version__",
    "from ",
    "#!/",
    "#  encodig",
]


def clean_text(text: str) -> str:
    """Remove lines containing any string from STRTOFIND."""
    return "\n".join(
        line for line in text.splitlines()
        if not any(s in line
                   for s in STRTOFIND)  # why: check substring membership
    )


def clean_file(path: str) -> None:
    """Remove Requires-Dist lines from a normal file."""
    try:
        with open(
                path,
                encoding="utf-8",
                errors="ignore",
        ) as f:
            original = f.read()
    except Exception:
        return

    cleaned = clean_text(original)
    if cleaned != original:  # only rewrite when changed
        with open(path, "w", encoding="utf-8") as f:
            f.write(cleaned)


def process_zip(path: str) -> None:
    """Rewrite a zip/whl file with cleaned metadata."""
    tmp = tempfile.mktemp(suffix=".zip")
    # why: zipfile cannot update files in place; must rewrite entire archive
    with (
            zipfile.ZipFile(path, "r") as zin,
            zipfile.ZipFile(tmp, "w") as zout,
    ):
        for item in zin.infolist():
            data = zin.read(item.filename)
            base = os.path.basename(item.filename)
            if base in TARGET_FILES:
                try:
                    text = data.decode("utf-8", errors="ignore")
                    cleaned = clean_text(text)
                    data = cleaned.encode("utf-8")
                except Exception:
                    pass
            zout.writestr(item, data)
    shutil.move(tmp, path)


def process_tar(path: str) -> None:
    """Rewrite a tar/tar.gz/tgz file with cleaned metadata."""
    tmp_dir = tempfile.mkdtemp()
    tmp_tar = tempfile.mktemp(suffix=".tar.gz")

    # extract all
    # why: tar does not support safe in-place mutation
    with tarfile.open(path, "r:*") as tar:
        tar.extractall(tmp_dir)

    # clean extracted files
    for root, _, files in os.walk(tmp_dir):
        for name in files:
            if name in TARGET_FILES:
                clean_file(os.path.join(root, name))

    # repack
    with tarfile.open(tmp_tar, "w:gz") as tar:
        tar.add(tmp_dir, arcname="")

    shutil.move(tmp_tar, path)
    shutil.rmtree(tmp_dir)


def dispatch_archive(path: str) -> None:
    """Detect archive type and process accordingly."""
    name = path.lower()
    if name.endswith(".zip") or name.endswith(".whl"):
        process_zip(path)
    elif name.endswith(".tar.gz") or name.endswith(".tgz") or name.endswith(
            ".tar"):
        process_tar(path)


def main() -> None:
    for root, _, files in os.walk("."):
        for name in files:
            full_path = os.path.join(root, name)

            # handle raw metadata files
            if dh.get_ext(full_path) in EXT:
                clean_file(full_path)
                continue

            # handle archives
            if name.lower().endswith((
                    ".zip",
                    ".whl",
                    ".tar.gz",
                    ".tgz",
                    ".tar",
            )):
                dispatch_archive(full_path)


if __name__ == "__main__":
    main()

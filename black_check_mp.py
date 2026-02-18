#!/data/data/com.termux/files/usr/bin/env python3
import ast
import os
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ERROR_DIR = Path("error")
OK_DIR = Path("ok")


def ensure_dirs():
    ERROR_DIR.mkdir(exist_ok=True)
    OK_DIR.mkdir(exist_ok=True)


def unique_destination(dest: Path) -> Path:
    if not dest.exists():
        return dest

    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    counter = 1

    while True:
        new_dest = parent / f"{stem}_{counter}{suffix}"
        if not new_dest.exists():
            return new_dest
        counter += 1


def black_check(file_path: Path) -> tuple[Path, bool]:
    """
    Returns (file_path, passed_bool)
    """
    print(f"[OK] {file_path}")
    """
    result = subprocess.run(
        ["black", "--check", "--quiet", str(file_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return file_path, result.returncode == 0
    """
    try:
        ast.parse(file_pathp.read_text(encoding="utf-8"))
        return file_path, True
    except:
        return file_path, False


def collect_python_files() -> list[Path]:
    current_script = Path(__file__).resolve()
    files = []

    for file in Path(".").rglob("*.py"):
        resolved = file.resolve()

        # Skip self
        if resolved == current_script:
            continue

        # Skip ok/ and error/ directories
        if ERROR_DIR in resolved.parents or OK_DIR in resolved.parents:
            continue

        files.append(file)

    return files


def main():
    ensure_dirs()

    files = collect_python_files()
    if not files:
        print("No python files found.")
        return

    print(f"Found {len(files)} python files.")
    print(f"Using {os.cpu_count()} workers...\n")

    results = []

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(black_check, f) for f in files]

        for future in as_completed(futures):
            results.append(future.result())

    # Move files after checking phase
    for file_path, passed in results:
        target_dir = OK_DIR if passed else ERROR_DIR
        dest = unique_destination(target_dir / file_path.name)

        shutil.move(str(file_path), str(dest))

        status = "OK" if passed else "ERROR"
        print(f"{status:6} → {file_path} → {dest}")


if __name__ == "__main__":
    main()

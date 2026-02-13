#!/data/data/com.termux/files/usr/bin/env python3
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm

SECONDS_24H = 24 * 60 * 60
NOW = time.time()
EXCLUDE_DIRS = {".git"}


def iter_files(root: Path) -> list[Path]:
    """Collect all files under root, excluding .git directories."""
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            files.append(Path(dirpath) / fname)
    return files


def ctime_if_recent(
    path: Path,
) -> tuple[float, Path] | None:
    """Return (ctime, path) if file was created/changed within last 24h."""
    try:
        ctime = path.stat().st_ctime
        if NOW - ctime <= SECONDS_24H:
            return ctime, path
    except (
        FileNotFoundError,
        PermissionError,
        OSError,
    ):
        pass
    return None


def main() -> None:
    root = Path.cwd()
    files = iter_files(root)

    if not files:
        return

    recent: list[tuple[float, Path]] = []

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(ctime_if_recent, p) for p in files]

        for fut in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Scanning",
            unit="file",
        ):
            result = fut.result()
            if result is not None:
                recent.append(result)

    # sort oldest → newest (newest last)
    recent.sort(key=lambda x: x[0])

    for _, path in recent:
        print(path.relative_to(root))


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/env python3
import argparse
from pathlib import Path

import regex as re

PKG_NAME_RE = re.compile(
    r"""
    ^\s*
    (?:
        -e\s+                # editable install
    )?
    (?P<name>[A-Za-z0-9_.\-]+)
    """,
    re.VERBOSE,
)


def extract_package_name(line: str) -> str | None:
    line = line.strip()

    # Skip empty lines and comments
    if not line or line.startswith("#"):
        return None

    # Skip direct references without a clear package name
    if line.startswith(("git+", "http://", "https://")):
        return None

    # Handle PEP 508 direct refs: pkg @ url
    if "@" in line:
        name = line.split("@", 1)[0].strip()
        return name if name else None

    # Handle normal cases: pkg==1.2.3, pkg>=1.0, etc.
    match = PKG_NAME_RE.match(line)
    if match:
        return match.group("name")

    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description=
        "Clean pip freeze output and keep only package names (overwrite file)."
    )
    parser.add_argument("file", help="pip freeze output file")
    args = parser.parse_args()

    path = Path(args.file)

    if not path.is_file():
        raise SystemExit(f"Error: file not found: {path}")

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

    packages = []
    for line in lines:
        name = extract_package_name(line)
        if name:
            packages.append(name)

    # Deduplicate while preserving order
    seen = set()
    cleaned = [p for p in packages if not (p in seen or seen.add(p))]

    path.write_text(
        "\n".join(cleaned) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

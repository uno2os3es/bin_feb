#!/data/data/com.termux/files/usr/bin/env python3
import subprocess
from collections.abc import Iterable
from pathlib import Path

import regex as re

REQUIREMENTS_FILE = Path("requirements.txt")
MISSING_PATTERN = re.compile(r"requires ([A-Za-z0-9_\-]+), which is not installed\.")


def run_pip_check() -> str:
    """Run `pip check` and return stdout."""
    result = subprocess.run(
        ["pip", "check"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def parse_missing_packages(
    pip_output: str,
) -> list[str]:
    """Extract missing package names from `pip check` output."""
    missing: set[str] = set()

    for line in pip_output.splitlines():
        match = MISSING_PATTERN.search(line)
        if match:
            missing.add(match.group(1))

    return sorted(missing)


def read_existing_requirements() -> set[str]:
    """Read existing requirements.txt if it exists."""
    if not REQUIREMENTS_FILE.exists():
        return set()

    return {
        line.strip() for line in REQUIREMENTS_FILE.read_text().splitlines() if line.strip() and not line.startswith("#")
    }


def save_to_requirements(
    packages: Iterable[str],
) -> None:
    """Merge missing packages into requirements.txt with unique entries."""
    existing = read_existing_requirements()
    merged = sorted(existing | set(packages))

    REQUIREMENTS_FILE.write_text("\n".join(merged) + "\n")
    print(f"✔️ Saved {len(packages)} new package(s). Total: {len(merged)} in requirements.txt")


def main() -> None:
    print("🔍 Running pip check...")
    output = run_pip_check()

    if not output:
        print("🎉 No issues found by pip check.")
        return

    print("🔎 Parsing missing packages...")
    missing_packages = parse_missing_packages(output)

    if not missing_packages:
        print("🎉 No missing libraries detected.")
        return

    print(f"⚠️ Missing packages detected: {missing_packages}")
    save_to_requirements(missing_packages)


if __name__ == "__main__":
    main()

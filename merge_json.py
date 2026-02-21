#!/data/data/com.termux/files/usr/bin/env python3
import json
from pathlib import Path
import sys


def load_json_object(path):
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def merge_json_files(files):
    merged = {}
    for file in files:
        path = Path(file)
        if not path.exists():
            print(f"Warning: skipping missing file {path}")
            continue
        try:
            merged.update(load_json_object(path))
        except Exception as e:
            print(f"Warning: {path}: {e}")
    return merged


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} file1.json file2.json [...]")
        sys.exit(1)
    merged = merge_json_files(sys.argv[1:])
    json.dump(
        merged,
        sys.stdout,
        indent=4,
        ensure_ascii=False,
        sort_keys=True,
    )
    print()
    out_file = "dic.json"
    with open(out_file, "w") as fj:
        json.dump(
            merged,
            fj,
            indent=4,
            ensure_ascii=True,
            sort_keys=True,
        )
    print(f"saved to {out_file}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path


def csv_to_json_map(csv_file):
    csv_path = Path(csv_file)

    if not csv_path.exists():
        print(f"Error: file not found: {csv_path}")
        sys.exit(1)

    json_path = csv_path.with_suffix(".json")
    result = {}

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)  # skip header

        if not header or len(header) < 2:
            print("Error: CSV must have at least two columns")
            sys.exit(1)

        for _row_num, row in enumerate(reader, start=2):
            if len(row) < 2:
                continue  # skip malformed rows

            key = row[0].strip()
            value = row[1].strip()

            if key:
                result[key] = value

    # Pretty JSON output (default)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            indent=4,
            ensure_ascii=False,
            sort_keys=True,
        )

    print(f"Converted (mapping JSON): {csv_path} → {json_path}")


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file.csv>")
        sys.exit(1)

    csv_to_json_map(sys.argv[1])


if __name__ == "__main__":
    main()

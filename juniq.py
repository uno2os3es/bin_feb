#!/data/data/com.termux/files/usr/bin/env python3
import json
import sys

if len(sys.argv) != 2:
    print("Usage: python dedup_json.py <json_file>")
    sys.exit(1)

fname = sys.argv[1]

with open(fname, encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, dict):
    raise ValueError("JSON must be an object (key-value pairs)")

unique = {}
for k, v in data.items():
    unique[k] = v

with open(fname, "w", encoding="utf-8") as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

print(f"updated: {fname}")

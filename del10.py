#!/data/data/com.termux/files/usr/bin/env python3
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    fname = sys.argv[1]
    llen = int(str(sys.argv[2]).strip()) if len(sys.argv) == 3 else 10
    lines = []
    try:
        with open(fname) as f:
            lines = f.readlines()

        filtered = [line for line in lines if len(line.strip()) >= llen]

        with open(fname, "w") as f:
            f.writelines(filtered)

    except FileNotFoundError:
        print(f"Error: File '{fname}' not found.")
    except Exception as e:
        print("An error occurred:", e)

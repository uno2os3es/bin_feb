#!/usr/bin/env python3
from pathlib import Path
from sys import argv, exit

from dh import file_size, format_size, run_command
from termcolor import cprint


def process_file(fp):
    start = file_size(fp)
    if not fp.exists():
        return False
    print(f"{fp.name}", end=" ")
    cmd = f"terser {fp}"
    output, err, code = run_command(cmd)
    if code == 0:
        fp.write_text(output)
        result = file_size(fp) - start
        if int(result) == 0:
            cprint("[OK]", "white")
        elif result < 0:
            cprint(f"[OK] - {format_size(abs(result))}", "cyan")
        elif result > 0:
            cprint(f"[OK] + {format_size(abs(result))}", "yellow")
        return True
    else:
        cprint(f"[ERROR] {err}", "magenta")
        return False


def main():
    fn=Path(argv[1])
    process_file(fn)

if __name__ == "__main__":
    exit(main())

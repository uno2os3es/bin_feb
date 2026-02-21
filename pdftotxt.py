#!/data/data/com.termux/files/usr/bin/env python3
import os
from pathlib import Path
import sys

import pdfplumber


def process_file(fp):
    i = 1
    with pdfplumber.open(fp) as pdf:
        for page in pdf.pages:
            text = page.extract_text(encoding="utf-8")
            outdir = Path(fp).stem
            if not os.path.exists(outdir):
                os.mkdir(outdir)
            if i < 10:
                txtfile = f"{outdir}/{Path(fp).stem}00{i!s}.txt"
            elif i < 100 and i >= 10:
                txtfile = f"{outdir}/{Path(fp).stem}0{i!s}.txt"
            else:
                txtfile = f"{outdir}/{Path(fp).stem}{i!s}.txt"
            with open(txtfile, "w") as fo:
                fo.write(text)
            print(f"{txtfile} created")
            i += 1


def main():
    process_file(sys.argv[1])


if __name__ == "__main__":
    main()

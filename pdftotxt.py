#!/data/data/com.termux/files/usr/bin/python
import os
import sys
from pathlib import Path

import pdfplumber


def process_file(fp):
    i = 1
    with pdfplumber.open(fp) as pdf:
        for page in pdf.pages:
            text = page.extract_text(encoding="utf-8")
            if not os.path.exists(Path(fp).stem):
                os.mkdir(outdir)
            txtfile = f"{outdir}/{Path(fp).stem}{i!s}.txt"
            with open(txtfile, "w") as fo:
                fo.write(text)
            del fo
            del text

            print(f"{txtfile} created")
            i += 1
            del page
    del i
    del pdf


def main():
    process_file(sys.argv[1])


if __name__ == "__main__":
    main()

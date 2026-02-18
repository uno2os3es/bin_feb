#!/data/data/com.termux/files/usr/bin/env python3
import os
from multiprocessing import Pool
from pathlib import Path

import pdfplumber
from termcolor import cprint


def process_file(fp):
    i = 1

    with pdfplumber.open(fp) as pdf:
        numpages = len(pdf.pages)
        strn = len(str(numpages))
        outdir = Path(fp).stem.replace(str(numpages), "")
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        for page in pdf.pages:
            stri = str(i)
            while len(stri) < strn:
                stri = "0" + stri
            txtfile = f"{outdir}/{stri}.txt"
            if os.path.exists(txtfile):
                print(f"{Path(txtfile).name} exists")
                i += 1
                continue
            text = page.extract_text(encoding="utf-8")
            if text:
                with open(txtfile, "w") as fo:
                    fo.write(text)
                cprint(f"{txtfile} created", "cyan")
            else:
                with open(txtfile, "w") as fo:
                    fo.write("empty page")
                cprint(f"page {i} is empty", "blue")
            i += 1

    del i
    del text
    del pages


def main():
    files = []
    for file in os.listdir("."):
        if file.endswith(".pdf"):
            files.append(file)
    if len(files) == 0:
        print("no pdf file found.")
        return
    pool = Pool(4)
    for f in files:
        _ = pool.apply_async(process_file, ((f),))
    pool.close()
    pool.join()
    del pool
    del files
    return


if __name__ == "__main__":
    main()

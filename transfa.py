#!/data/data/com.termux/files/usr/bin/env python3
import os
from pathlib import Path
import sys

from deep_translator import GoogleTranslator


def translate_file(fname: str):
    linez = []
    fpath = Path(fname)
    with Path(fpath).open("r", encoding="utf-8") as infile:
        linez = infile.readlines()
    outf = str(fpath.name) + "_eng" + str(fpath.suffix)
    outpath = os.path.join(fpath.parent, outf)
    with Path(outpath).open("a", encoding="utf-8") as f:
        for line in linez:
            if line.strip():
                text = line.strip()
                translator = GoogleTranslator(source="fa", target="en")
                result = translator.translate(text)
                f.write(f"\n{text} = {result}\n")
    return result


if __name__ == "__main__":
    translate_file(sys.argv[1])

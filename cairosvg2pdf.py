#!/data/data/com.termux/files/usr/bin/env python3
import sys

import cairosvg

infile = sys.argv[1]
outfile = infile.replace(".svg", ".pdf")
cairosvg.svg2pdf(url=infile, write_to=outfile)

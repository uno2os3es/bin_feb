#!/data/data/com.termux/files/usr/bin/env python3
import sys

import epub

c = epub.open_epub(sys.argv[1])
c.extractall()

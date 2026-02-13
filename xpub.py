#!/usr/bin/env python
import sys

import epub

c = epub.open_epub(sys.argv[1])
c.extractall()

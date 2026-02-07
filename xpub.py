#!/usr/bin/env python
import epub

c = epub.open_epub("file.epub")
c.extractall()

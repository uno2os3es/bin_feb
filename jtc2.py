#!/data/data/com.termux/files/usr/bin/env python3
import ast
import os
from sys import argv
from pathlib import Path
from dh import run_command

if __name__=="__main__":
    path=Path(argv[1])
    orig_code=path.read_text(encoding="utf-8")
    if path.suffix=='.rs':
        cmd=f"just-the-code -s {str(path)}"

    elif path.suffix=='.py':
        cmd=f"just-the-code -s --language=python {str(path)}"

    ret,new_code,err=run_command(cmd)
    if ret==0 and len(orig_code)!=len(new_code):
        if path.suffix=='.py':
            try:
                tree=ast.parse(new_code)
                path.write_text(new_code,encoding="utf-8")
            except:
                print("error")
        else:
            path.write_text(new_code,encoding="utf-8")


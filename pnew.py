#!/data/data/com.termux/files/usr/bin/env python3
from sys import argv


def main():
    fn = argv[1]
    template = """#!/usr/bin/env python
from sys import exit
from time import perf_counter
import os
def process_file(fp) -> None:
    nl=[]
    with open(fp,'r') as f:
        lines=f.readlines()
        for line in lines:
            if :
                nl.append(line)
    with open(fp,'w') as fo:
        for k in nl:
            fo.write(k)
def main() -> None:
    start=perf_counter()
    for pth in os.listdir('.'):
        process_file(pth)
    print(f'{perf_counter()-start} seconds')
if __name__=='__main__':
    exit(main())
"""
    with open(fn, "w") as f:
        f.write(template)
    print(f"{fn} created.")


if __name__ == "__main__":
    main()

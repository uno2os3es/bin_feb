#!/data/data/com.termux/files/usr/bin/env python3
import sys
import tokenize
from io import StringIO

import regex as re

python_keywords = {
    "def",
    "class",
    "import",
    "from",
    "lambda",
    "yield",
    "async",
    "await",
}


def is_probably_python(lines):
    score = 0
    for line in lines:
        if any(kw in line for kw in python_keywords):
            score += 1
        if re.search(r":\s*$", line):  # colon endings
            score += 1
        if re.match(r"\s{4}", line):  # indentation
            score += 1
    return score >= 2  # threshold


def looks_like_python(code_block) -> bool | None:
    try:
        tokenize.generate_tokens(StringIO(code_block).readline)
        return True
    except tokenize.TokenError:
        return False


def is_python_like(line) -> bool:
    if re.match(
        r"\s*(def|class|if|elif|else|for|while|try|except|with)\b.*:",
        line,
    ):
        return True
    if re.match(r"\s*@[A-Za-z_]\w*", line):  # decorators
        return True
    if re.match(r"\s*import\b|\s*from\b", line):  # imports
        return True
    return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fpy.py <filename>")
        sys.exit(1)

    fname = sys.argv[1]

    try:
        with open(fname) as f:
            lines = f.readlines()
        #        prob=[]
        #        for x in lines:
        #            if is_probably_python(x):
        #                prob.append(x)
        #        with open("prob.py","w") as fp:
        #            fp.writelines(prob)
        filtered = []

        for line in lines:
            if is_python_like(line) or looks_like_python(line) or is_probably_python(line):
                filtered.append(line)
        print(filtered)
        with open("out.py", "w") as f:
            for l in filtered:
                f.write(l)
                f.write("\n")

    except FileNotFoundError:
        print(f"Error: File '{fname}' not found.")
    except Exception as e:
        print("An error occurred:", e)

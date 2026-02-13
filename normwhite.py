#!/data/data/com.termux/files/usr/bin/env python3
import sys


def normalize_white_space(input_path) -> None:
    with pathlib.Path(input_path).open("r", encoding="utf-8",
                                       errors="replace") as f:
        text = f.read()
    cleaned = re.sub(
        r"[\u00A0\u2000-\u200F\u2028\u2029\u202F\u205F\u3000\uFEFF]",
        " ",
        text,
    )
    cleaned = re.sub(r"[\u200B-\u200D\uFEFF]", "", cleaned)
    with pathlib.Path(input_path).open("w", encoding="utf-8") as f:
        f.write(cleaned)


if __name__ == "__main__":
    fname = sys.argv[1]
    normalize_white_space(fname)

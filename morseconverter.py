#!/data/data/com.termux/files/usr/bin/env python3
import argparse
import pathlib
import sys

MORSE_CODE_DICT = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    "0": "-----",
    " ": "/",
}
REVERSE_MORSE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}


def text_to_morse(text):
    """Convert text to Morse code."""
    morse = []
    for char in text.upper():
        if char in MORSE_CODE_DICT:
            morse.append(MORSE_CODE_DICT[char])
        else:
            morse.append(char)
    return " ".join(morse)


def morse_to_text(morse):
    """Convert Morse code to text."""
    text = []
    morse_chars = morse.split(" ")
    for code in morse_chars:
        if code in REVERSE_MORSE_DICT:
            text.append(REVERSE_MORSE_DICT[code])
        elif code:
            text.append(code)
    return "".join(text)


def encrypt_file(input_filename, output_filename) -> None:
    """Read file and convert to Morse code."""
    try:
        with pathlib.Path(input_filename).open("r", encoding="utf-8") as infile:
            content = infile.read()
        morse_content = text_to_morse(content)
        with pathlib.Path(output_filename).open("w", encoding="utf-8") as outfile:
            outfile.write(morse_content)
    except FileNotFoundError:
        sys.exit(1)
    except Exception:
        sys.exit(1)


def decrypt_file(input_filename, output_filename) -> None:
    """Read Morse code file and convert to text."""
    try:
        with pathlib.Path(input_filename).open("r", encoding="utf-8") as infile:
            morse_content = infile.read()
        text_content = morse_to_text(morse_content)
        with pathlib.Path(output_filename).open("w", encoding="utf-8") as outfile:
            outfile.write(text_content)
    except FileNotFoundError:
        sys.exit(1)
    except Exception:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Morse Code Encryptor/Decryptor")
    parser.add_argument("input_file", help="Input file name")
    parser.add_argument("output_file", help="Output file name")
    parser.add_argument(
        "--encrypt",
        action="store_true",
        help="Encrypt text to Morse code",
    )
    parser.add_argument(
        "--decrypt",
        action="store_true",
        help="Decrypt Morse code to text",
    )
    args = parser.parse_args()
    if args.encrypt and args.decrypt:
        sys.exit(1)
    if not args.encrypt and not args.decrypt:
        sys.exit(1)
    if args.encrypt:
        encrypt_file(args.input_file, args.output_file)
    elif args.decrypt:
        decrypt_file(args.input_file, args.output_file)


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/env python3
import sys

import PyPDF2


def extract_text_from_pdf(pdf_filename):
    with open(pdf_filename, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)

        extracted_text = ""

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            extracted_text += page.extract_text()

    return extracted_text


def save_text_to_file(text, output_filename):
    with open(output_filename, "w", encoding="utf-8") as text_file:
        text_file.write(text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_pdf_text.py <pdf_filename>")
        sys.exit(1)

    pdf_filename = sys.argv[1]
    text_filename = pdf_filename.replace(".pdf", ".txt")

    extracted_text = extract_text_from_pdf(pdf_filename)

    save_text_to_file(extracted_text, text_filename)

    print(f"Text extracted and saved to {text_filename}")

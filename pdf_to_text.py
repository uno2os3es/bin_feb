#!/data/data/com.termux/files/usr/bin/env python3
import sys

import PyPDF2


def extract_text_from_pdf(pdf_filename):
    # Open the PDF file in read-binary mode
    with open(pdf_filename, "rb") as file:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(file)

        # Initialize text variable
        extracted_text = ""

        # Loop through all pages and extract text
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            extracted_text += page.extract_text()

    return extracted_text


def save_text_to_file(text, output_filename):
    # Write the extracted text to a text file
    with open(output_filename, "w", encoding="utf-8") as text_file:
        text_file.write(text)


if __name__ == "__main__":
    # Get the PDF filename from command line argument
    if len(sys.argv) != 2:
        print("Usage: python extract_pdf_text.py <pdf_filename>")
        sys.exit(1)

    pdf_filename = sys.argv[1]
    text_filename = pdf_filename.replace(".pdf", ".txt")

    # Extract text from the PDF
    extracted_text = extract_text_from_pdf(pdf_filename)

    # Save extracted text to a text file
    save_text_to_file(extracted_text, text_filename)

    print(f"Text extracted and saved to {text_filename}")

#!/data/data/com.termux/files/usr/bin/env python3
import os


def create_html_template(filename="index.html"):
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <!-- Your content here -->
</body>
</html>
"""
    try:
        with open(filename, "w") as f:
            f.write(html_template)
        print(f"Successfully created {filename} in {os.getcwd()}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    create_html_template()

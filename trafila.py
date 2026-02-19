#!/data/data/com.termux/files/usr/bin/env python3
import sys
from pathlib import Path

import trafilatura


def convert_to_md(html_file: Path):
    """Convert HTML to Markdown using trafilatura for better content extraction."""
    try:
        html_content = html_file.read_text(encoding="utf-8")

        markdown = trafilatura.extract(
            html_content,
            output_format="markdown",
            include_links=True,
            include_images=True,
            include_tables=True,
            no_fallback=False,
        )

        if markdown:
            md_file = html_file.with_suffix(".md")
            md_file.write_text(markdown, encoding="utf-8")
            print(f"✓ Converted: {html_file.name} -> {md_file.name}")
            return (md_file, True)
        else:
            print(f"✗ No content extracted from {html_file.name}")
            return (html_file, False)
    except Exception as e:
        print(f"✗ Error: {e}")
        return (html_file, False)


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    convert_to_md(fn)

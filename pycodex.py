#!/data/data/com.termux/files/usr/bin/env python3
"""Extract Python code blocks from HTML files with support for local files, URLs, and Canvas.
Saves each code block to a separate file with intelligent naming.
Includes concurrent.futures for faster extraction from multiple files.
"""

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import regex as re
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class CodeBlock:
    """Represents an extracted code block."""

    content: str
    language: str
    source_file: str
    block_index: int
    suggested_name: str | None = None


class HTTPSession:
    """Manage HTTP requests with retry strategy."""

    def __init__(self, max_retries=3, timeout=10) -> None:
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429][500][502][503][504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.timeout = timeout

    def fetch(self, url: str) -> str | None:
        """Fetch content from URL."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def close(self) -> None:
        self.session.close()


class CodeBlockExtractor:
    """Extract Python code blocks from HTML content."""

    def __init__(self) -> None:
        self.http_session = HTTPSession()

    def extract_from_html(self, html_content: str,
                          source_file: str) -> list[CodeBlock]:
        """Extract Python code blocks from HTML content."""
        soup = BeautifulSoup(html_content, "html.parser")
        code_blocks = []
        # Extract from standard <pre><code> blocks
        code_blocks.extend(self._extract_from_pre_code(soup, source_file))
        # Extract from <code> blocks
        code_blocks.extend(self._extract_from_code_tags(soup, source_file))
        # Extract from Canvas (JSON embedded in script tags)
        code_blocks.extend(self._extract_from_canvas(soup, source_file))
        return code_blocks

    def _extract_from_pre_code(
        self,
        soup: BeautifulSoup,
        source_file: str,
    ) -> list[CodeBlock]:
        """Extract from <pre><code> tags."""
        blocks = []
        for idx, pre in enumerate(soup.find_all("pre")):
            code = pre.find("code")
            if code:
                content = code.get_text()
                if self._is_python_code(content):
                    block = CodeBlock(
                        content=content,
                        language="python",
                        source_file=source_file,
                        block_index=idx,
                        suggested_name=self._extract_filename_from_code(
                            content),
                    )
                    blocks.append(block)
        return blocks

    def _extract_from_code_tags(
        self,
        soup: BeautifulSoup,
        source_file: str,
    ) -> list[CodeBlock]:
        """Extract from standalone <code> tags."""
        blocks = []
        offset = len(soup.find_all("pre"))
        for idx, code in enumerate(soup.find_all("code")):
            # Skip if already inside <pre>
            if code.parent.name == "pre":
                continue
            content = code.get_text()
            if self._is_python_code(content):
                block = CodeBlock(
                    content=content,
                    language="python",
                    source_file=source_file,
                    block_index=offset + idx,
                    suggested_name=self._extract_filename_from_code(content),
                )
                blocks.append(block)
        return blocks

    def _extract_from_canvas(
        self,
        soup: BeautifulSoup,
        source_file: str,
    ) -> list[CodeBlock]:
        """Extract Python code from Canvas LMS embedded content."""
        blocks = []
        offset = len(soup.find_all("pre")) + len(soup.find_all("code"))
        for idx, script in enumerate(soup.find_all("script")):
            if script.get("type") == "application/json" or "canvas" in str(
                    script.get("id", "")).lower():
                try:
                    content = script.string
                    if content:
                        # Try to parse as JSON
                        data = json.loads(content)
                        # Recursively search for Python code in JSON structure
                        python_code = self._extract_from_json(data)
                        if python_code:
                            for py_code in python_code:
                                if self._is_python_code(py_code):
                                    block = CodeBlock(
                                        content=py_code,
                                        language="python",
                                        source_file=source_file,
                                        block_index=offset + idx,
                                        suggested_name=self.
                                        _extract_filename_from_code(py_code),
                                    )
                                    blocks.append(block)
                except (
                        json.JSONDecodeError,
                        TypeError,
                ):
                    pass
        return blocks

    def _extract_from_json(self, data, depth=0, max_depth=5) -> list[str]:
        """Recursively extract strings that might be Python code from JSON."""
        if depth > max_depth:
            return []
        python_codes = []
        if isinstance(data, dict):
            for value in data.values():
                python_codes.extend(
                    self._extract_from_json(
                        value,
                        depth + 1,
                        max_depth,
                    ))
        elif isinstance(data, list):
            for item in data:
                python_codes.extend(
                    self._extract_from_json(item, depth + 1, max_depth))
        elif isinstance(data, str):
            # Check if string contains Python code indicators
            if any(keyword in data for keyword in [
                    "def ",
                    "import ",
                    "class ",
                    "if __name__",
            ]):
                python_codes.append(data)
        return python_codes

    def _is_python_code(self, content: str) -> bool:
        """Determine if content is likely Python code."""
        if not content.strip():
            return False
        python_keywords = [
            "def ",
            "class ",
            "import ",
            "from ",
            "if ",
            "for ",
            "while ",
            "try:",
            "except",
            "with ",
            "lambda",
            "return ",
            "yield ",
            "async ",
            "await ",
            "@",
            "elif ",
            "else:",
            "self.",
        ]
        content_lower = content.lower()
        keyword_count = sum(1 for keyword in python_keywords
                            if keyword.lower() in content_lower)
        # Also check for common Python syntax patterns
        python_patterns = [
            r"\bdef\s+\w+\s*\(",
            r"\bclass\s+\w+",
            r"\bif\s+.*:",
            r"\bfor\s+.*\s+in\s+",
            r"\bimport\s+",
            r"\breturn\s+",
            r"\b(True|False|None)\b",
        ]
        pattern_matches = sum(1 for pattern in python_patterns
                              if re.search(pattern, content))
        return keyword_count >= 2 or pattern_matches >= 2

    def _extract_filename_from_code(self, content: str) -> str | None:
        """Try to extract a suggested filename from code comments."""
        lines = content.split("\n")
        # Look for filename in first few lines
        for line in lines[:10]:
            # Check for patterns like:
            # # filename.py
            # # filename: script.py
            # # name: my_script.py
            match = re.search(
                r"#\s*(?:filename|name|file)\s*:?\s*([\w\-._]+\.py)",
                line,
                re.IGNORECASE,
            )
            if match:
                return match.group(1)
        return None

    def close(self) -> None:
        """Cleanup resources."""
        self.http_session.close()


class FileProcessor:
    """Process HTML files and extract code blocks."""

    def __init__(self, output_dir: str = "./output") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = CodeBlockExtractor()

    def process_file(self, file_path: str) -> int:
        """Process a single HTML file and save extracted code blocks."""
        try:
            file_path = Path(file_path)
            if file_path.suffix.lower() != ".html":
                return 0
            with open(
                    file_path,
                    encoding="utf-8",
                    errors="ignore",
            ) as f:
                html_content = f.read()
            code_blocks = self.extractor.extract_from_html(
                html_content, str(file_path))
            if code_blocks:
                self._save_code_blocks(code_blocks, file_path)
                logger.info(
                    f"Extracted {len(code_blocks)} code blocks from {file_path}"
                )
            return len(code_blocks)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return 0

    def process_url(self, url: str) -> int:
        """Process an HTML file from URL and save extracted code blocks."""
        try:
            html_content = self.extractor.http_session.fetch(url)
            if not html_content:
                return 0
            code_blocks = self.extractor.extract_from_html(html_content, url)
            if code_blocks:
                self._save_code_blocks(code_blocks, url)
                logger.info(
                    f"Extracted {len(code_blocks)} code blocks from {url}")
            return len(code_blocks)
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return 0

    def _save_code_blocks(
        self,
        code_blocks: list[CodeBlock],
        source: str,
    ) -> None:
        """Save code blocks to separate files with intelligent naming."""
        source_name = Path(
            source).stem if not source.startswith("http") else "url_content"
        source_dir = self.output_dir / source_name
        source_dir.mkdir(parents=True, exist_ok=True)
        for block in code_blocks:
            # Determine filename
            filename = block.suggested_name or f"{source_name}_block_{block.block_index:03d}.py"
            # Ensure unique filename
            filepath = source_dir / filename
            counter = 1
            original_filepath = filepath
            while filepath.exists():
                name_parts = original_filepath.stem.rsplit("_", 1)
                if len(name_parts) == 2 and name_parts[1].isdigit():
                    base_name = name_parts[0]
                else:
                    base_name = original_filepath.stem
                filepath = source_dir / f"{base_name}_{counter}.py"
                counter += 1
            # Save the code block
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(block.content)
            logger.debug(f"Saved code block to {filepath}")

    def close(self) -> None:
        """Cleanup resources."""
        self.extractor.close()


def find_html_files(directory: str) -> list[str]:
    """Recursively find all HTML files in a directory."""
    html_files = []
    path = Path(directory)
    for html_file in path.rglob("*.html"):
        html_files.append(str(html_file))
    return html_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract Python code blocks from HTML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from a single file
  python script.py -f document.html
  # Extract from all HTML files in a directory
  python script.py -p /path/to/documents
  # Extract from a URL
  python script.py -u https://example.com/page.html
  # Extract from current directory (default)
  python script.py
        """,
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Path to a single HTML file",
    )
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        help="Path to directory containing HTML files",
    )
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        help="URL to fetch HTML content from",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="./output",
        help="Output directory for extracted code blocks (default: ./output)",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=5,  # Default number of threads
        help="Number of parallel jobs (default: 5)",
    )
    args = parser.parse_args()
    processor = FileProcessor(output_dir=args.output)
    total_blocks = 0
    try:
        if args.url:
            # Process URL
            logger.info(f"Processing URL: {args.url}")
            total_blocks += processor.process_url(args.url)
        elif args.file:
            # Process single file
            logger.info(f"Processing file: {args.file}")
            total_blocks += processor.process_file(args.file)
        elif args.path:
            # Process directory
            logger.info(f"Processing directory: {args.path}")
            html_files = find_html_files(args.path)
            if html_files:
                logger.info(f"Found {len(html_files)} HTML files")
                with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                    futures = {
                        executor.submit(
                            processor.process_file,
                            file,
                        ): file
                        for file in html_files
                    }
                    for future in as_completed(futures):
                        total_blocks += future.result()
            else:
                logger.warning(f"No HTML files found in {args.path}")
        else:
            # Process current directory (default)
            logger.info(
                "Processing HTML files in current directory recursively")
            html_files = find_html_files(".")
            if html_files:
                logger.info(f"Found {len(html_files)} HTML files")
                with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                    futures = {
                        executor.submit(
                            processor.process_file,
                            file,
                        ): file
                        for file in html_files
                    }
                    for future in as_completed(futures):
                        total_blocks += future.result()
            else:
                logger.warning("No HTML files found in current directory")
        logger.info(f"Total code blocks extracted: {total_blocks}")
        logger.info(f"Results saved to: {processor.output_dir}")
    finally:
        processor.close()


if __name__ == "__main__":
    main()

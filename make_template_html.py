#!/usr/bin/env python3
"""
Create a template HTML file by processing all HTML files in current directory recursively.
Extracts common structure and merges content into template.html
"""

from pathlib import Path

from bs4 import BeautifulSoup


def find_html_files(root_dir: str = ".") -> list[Path]:
    """
    Recursively find all HTML files in the directory.

    Args:
        root_dir: Root directory to search from

    Returns:
        List of Path objects for HTML files
    """
    html_files = []
    root_path = Path(root_dir).resolve()

    for file_path in root_path.rglob("*.html"):
        # Skip template.html if it already exists
        if file_path.name != "template.html":
            html_files.append(file_path)

    for file_path in root_path.rglob("*.htm"):
        html_files.append(file_path)

    return sorted(html_files)


def extract_common_structure(html_files: list[Path]) -> dict:
    """
    Analyze HTML files to extract common structure elements.

    Args:
        html_files: List of HTML file paths

    Returns:
        Dictionary containing common structure information
    """
    body_classes = []
    meta_tags = []
    link_tags = []
    script_tags = []

    for file_path in html_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")

                # Extract head elements
                if soup.head:
                    for meta in soup.head.find_all("meta"):
                        meta_tags.append(str(meta))
                    for link in soup.head.find_all("link"):
                        link_tags.append(str(link))
                    for script in soup.head.find_all("script"):
                        if script.get("src"):
                            script_tags.append(str(script))

                # Extract body classes
                if soup.body and soup.body.get("class"):
                    body_classes.extend(soup.body.get("class"))

        except Exception as e:
            print(f"⚠️  Error processing {file_path}: {e}")

    # Find most common elements
    common_meta = list(set(meta_tags))
    common_links = list(set(link_tags))
    common_scripts = list(set(script_tags))
    common_body_class = " ".join(set(body_classes)) if body_classes else ""

    return {
        "meta_tags": common_meta,
        "link_tags": common_links,
        "script_tags": common_scripts,
        "body_class": common_body_class,
    }


def merge_html_content(html_files: list[Path]) -> str:
    """
    Merge content from all HTML files.

    Args:
        html_files: List of HTML file paths

    Returns:
        Merged HTML content as string
    """
    merged_sections = []

    for file_path in html_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")

                # Extract body content
                content = soup.body.decode_contents() if soup.body else str(soup)

                # Create section with file reference
                section_html = f"""
    <!-- Content from: {file_path.relative_to(Path.cwd())} -->
    <section class="merged-content" data-source="{file_path.name}">
        {content}
    </section>
"""
                merged_sections.append(section_html)

        except Exception as e:
            print(f"⚠️  Error merging {file_path}: {e}")

    return "\n".join(merged_sections)


def create_template_html(
    html_files: list[Path], output_file: str = "template.html", title: str = "Merged HTML Template"
) -> bool:
    """
    Create template HTML file from all HTML files in directory.

    Args:
        html_files: List of HTML file paths
        output_file: Output filename
        title: Page title

    Returns:
        True if successful, False otherwise
    """
    if not html_files:
        print("⚠️  No HTML files found")
        return False

    print(f"📄 Processing {len(html_files)} HTML files...")

    # Extract common structure
    structure = extract_common_structure(html_files)

    # Merge content
    merged_content = merge_html_content(html_files)

    # Build template HTML
    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>

    <!-- Common Meta Tags -->
    {chr(10).join("    " + tag for tag in structure["meta_tags"])}

    <!-- Common Stylesheets -->
    {chr(10).join("    " + tag for tag in structure["link_tags"])}

    <!-- Template Styles -->
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}

        .merged-content {{
            margin-bottom: 40px;
            padding: 20px;
            border-left: 4px solid #007bff;
            background: #f9f9f9;
        }}

        .merged-content::before {{
            content: attr(data-source);
            display: block;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 10px;
            font-size: 0.9em;
        }}

        h1, h2, h3 {{
            color: #333;
        }}

        .toc {{
            background: #e9ecef;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
        }}

        .toc h2 {{
            margin-top: 0;
        }}

        .toc ul {{
            list-style: none;
            padding-left: 0;
        }}

        .toc li {{
            margin: 5px 0;
        }}

        .toc a {{
            color: #007bff;
            text-decoration: none;
        }}

        .toc a:hover {{
            text-decoration: underline;
        }}
    </style>

    <!-- Common Scripts -->
    {chr(10).join("    " + tag for tag in structure["script_tags"])}
</head>
<body{' class="' + structure["body_class"] + '"' if structure["body_class"] else ""}>
    <div class="container">
        <h1>{title}</h1>

        <!-- Table of Contents -->
        <div class="toc">
            <h2>📑 Table of Contents</h2>
            <ul>
{chr(10).join(f'                <li><a href="#{Path(f).stem}">{Path(f).relative_to(Path.cwd())}</a></li>' for f in html_files)}
            </ul>
        </div>

        <!-- Merged Content -->
{merged_content}
    </div>

    <!-- Template Scripts -->
    <script>
        // Add smooth scrolling
        document.querySelectorAll('.toc a').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth' }});
                }}
            }});
        }});

        // Add IDs to sections for navigation
        document.querySelectorAll('.merged-content').forEach((section, index) => {{
            const source = section.getAttribute('data-source');
            const id = source.replace(/\\.html?$/, '');
            section.id = id;
        }});
    </script>
</body>
</html>
"""

    # Write template file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(template)

        print(f"✅ Template created successfully: {output_file}")
        print(f"📊 Merged {len(html_files)} HTML files")
        return True

    except Exception as e:
        print(f"❌ Error writing template: {e}")
        return False


def main():
    """Main function to create template HTML."""
    print("🔍 Searching for HTML files in current directory...")

    # Find all HTML files
    html_files = find_html_files()

    if not html_files:
        print("❌ No HTML files found in current directory")
        return

    print(f"📁 Found {len(html_files)} HTML files:")
    for file_path in html_files[:10]:  # Show first 10
        print(f"   - {file_path.relative_to(Path.cwd())}")
    if len(html_files) > 10:
        print(f"   ... and {len(html_files) - 10} more")

    # Create template
    success = create_template_html(html_files, output_file="template.html", title="Merged HTML Template")

    if success:
        print("\n" + "=" * 60)
        print("✨ Template generation complete!")
        print("📄 Output file: template.html")
        print("=" * 60)


if __name__ == "__main__":
    # Install BeautifulSoup if needed
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("📦 Installing BeautifulSoup4...")
        import subprocess
        import sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
        from bs4 import BeautifulSoup

    main()

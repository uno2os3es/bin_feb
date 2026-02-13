#!/usr/bin/env python3
"""
Convert JavaScript code to Python using AI-powered translation.
Uses OpenAI API or local AST-based conversion with js2py library.
"""

import argparse
import os
import sys
from pathlib import Path

import regex as re


def install_js2py():
    """Install js2py library if not available."""
    try:
        import js2py

        return True
    except ImportError:
        print("📦 Installing js2py library...")
        import subprocess

        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "js2py"])
            print("✅ js2py installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install js2py")
            return False


def convert_with_js2py(js_file: Path, outfile: Path) -> bool:
    """
    Convert JavaScript to Python using js2py library.
    """
    try:
        import js2py

        js2py.translate_file(js_file, out_file)

        return True

    except Exception as e:
        return (False, f"js2py conversion error: {e!s}")


def convert_with_openai(js_code: str,
                        api_key: str | None = None) -> tuple[bool, str]:
    """
    Convert JavaScript to Python using OpenAI API.

    Args:
        js_code: JavaScript source code
        api_key: OpenAI API key (optional, reads from env if not provided)

    Returns:
        Tuple of (success, converted_code_or_error)
    """
    try:
        import openai
    except ImportError:
        return (
            False,
            "OpenAI library not installed. Install with: pip install openai")

    # Get API key from parameter or environment
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return (
            False,
            "OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass --api-key",
        )

    try:
        client = openai.OpenAI(api_key=api_key)

        prompt = f"""Convert the following JavaScript code to Python.
Preserve the logic and functionality while using Pythonic idioms.
Only return the Python code without explanations.

JavaScript code:
```javascript
{js_code}
python code:"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role":
                    "system",
                    "content":
                    "You are an expert programmer who converts JavaScript to Python accurately.",
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        python_code = response.choices[0].message.content

        # Extract code from markdown if present
        if "```python" in python_code:
            python_code = re.search(r"```python\n(.*?)```", python_code,
                                    re.DOTALL)
            if python_code:
                python_code = python_code.group(1)
        elif "```" in python_code:
            python_code = re.search(r"```\n(.*?)```", python_code, re.DOTALL)
            if python_code:
                python_code = python_code.group(1)

        return (True, python_code.strip())

    except Exception as e:
        return (False, f"OpenAI API error: {e!s}")


def simple_js_to_python(js_code: str) -> str:
    """
    Simple rule-based JavaScript to Python converter.
    Handles basic syntax transformations.
    """
    python_code = js_code

    # Variable declarations
    python_code = re.sub(r"\b(let|const|var)\s+", "", python_code)

    # Console.log to print
    python_code = re.sub(r"console\.log\s*\(", "print(", python_code)

    # Boolean values
    python_code = re.sub(r"\btrue\b", "True", python_code)
    python_code = re.sub(r"\bfalse\b", "False", python_code)

    # Null/undefined to None
    python_code = re.sub(r"\b(null|undefined)\b", "None", python_code)

    # Function declarations
    python_code = re.sub(r"\bfunction\s+(\w+)\s*\((.*?)\)\s*{", r"def \1(\2):",
                         python_code)

    # Arrow functions (simple cases)
    python_code = re.sub(r"const\s+(\w+)\s*=\s*\((.*?)\)\s*=>\s*{",
                         r"def \1(\2):", python_code)
    python_code = re.sub(r"(\w+)\s*=\s*\((.*?)\)\s*=>\s*{", r"def \1(\2):",
                         python_code)

    # Comments
    python_code = re.sub(r"//", "#", python_code)

    # Remove semicolons
    python_code = re.sub(r";$", "", python_code, flags=re.MULTILINE)

    # Braces to colons (basic)
    python_code = re.sub(r"\s*{\s*$", ":", python_code, flags=re.MULTILINE)
    python_code = re.sub(r"^\s*}\s*$", "", python_code, flags=re.MULTILINE)

    # Control structures
    python_code = re.sub(r"\bif\s*\((.*?)\)\s*{", r"if \1:", python_code)
    python_code = re.sub(r"\belse\s+if\s*\((.*?)\)\s*{", r"elif \1:",
                         python_code)
    python_code = re.sub(r"\belse\s*{", r"else:", python_code)
    python_code = re.sub(r"\bwhile\s*\((.*?)\)\s*{", r"while \1:", python_code)

    # For loops (basic range conversion)
    return re.sub(
        r"for\s*\(\s*let\s+(\w+)\s*=\s*(\d+)\s*;\s*\1\s*<\s*(\w+)\s*;\s*\1\+\+\s*\)\s*{",
        r"for \1 in range(\2, \3):",
        python_code,
    )


def convert_file(
    input_file: Path,
    output_file: Path | None = None,
    method: str = "js2py",
    api_key: str | None = None,
) -> bool:
    """
    convert js file to python

    Args:
    input_file: Path to JavaScript file
    output_file: Path to output Python file (optional)
    method: Conversion method ('js2py', 'openai', or 'simple')
    api_key: OpenAI API key (for 'openai' method)

    Returns:
    True if successful, False otherwise
    """
    # Read JavaScript code
    try:
        with open(input_file, encoding="utf-8") as f:
            js_code = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    print(f"📄 Converting: {input_file}")
    print(f"🔧 Method: {method}")

    # Convert based on method
    if method == "js2py":
        if not install_js2py():
            print("⚠️  Falling back to simple conversion")
            method = "simple"
        else:
            output_file = input_file.with_suffix(".py")
            success = convert_with_js2py(input_file, output_file)
            return True

    if method == "openai":
        success, result = convert_with_openai(js_code, api_key)

    elif method == "simple":
        result = simple_js_to_python(js_code)
        success = True

    if not success:
        print(f"❌ Conversion failed: {result}")
        return False

    # Determine output file
    if output_file is None:
        output_file = input_file.with_suffix(".py")

    # Write Python code
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ Converted successfully: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        return False


def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(
        description="Convert JavaScript code to Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
             Examples:
                 Convert using js2py (default)
                     python js_to_py.py script.js
                 Convert using OpenAI API
                     python js_to_py.py script.js --method openai --api-key YOUR_KEY
                 Convert using simple rule-based method
                     python js_to_py.py script.js --method simple
                 Specify output file
                     python js_to_py.py script.js -o output.py
        """,
    )
    parser.add_argument("input", type=Path, help="Input JavaScript file")

    parser.add_argument(
        "-m",
        "--method",
        choices=["js2py", "openai", "simple"],
        default="simple",
        help="Conversion method (default: js2py)",
    )

    parser.add_argument(
        "--api-key",
        help=
        "OpenAI API key (for openai method, or set OPENAI_API_KEY env var)",
    )
    args = parser.parse_args()

    # Check if input file exists
    if not args.input.exists():
        print(f"❌ Error: File not found: {args.input}")
        sys.exit(1)

    # Convert file
    outputfile = str(args.input).replace(".js", ".py")
    success = convert_file(args.input, outputfile, args.method, args.api_key)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

## **Usage Examples**
"""
### **1. Basic Conversion (js2py method)**<span class="footnote-wrapper">[6](6)[8](8)</span>
```bash
python js_to_py.py script.js

2. Using OpenAI API
# Set API key as environment variable
export OPENAI_API_KEY="your-api-key-here"
python js_to_py.py script.js --method openai

# Or pass directly
python js_to_py.py script.js --method openai --api-key "your-key"

3. Simple Rule-Based Conversion
python js_to_py.py script.js --method simple

4. Specify Output File
python js_to_py.py input.js -o converted.py

Conversion Methods Comparison
1. js2py Method
Pros:

Full ECMAScript 5.1 support
Handles complex JavaScript features
No API costs
Works offline

Cons:

Generated code may not be idiomatic Python
Large files take time to translate
Some edge cases may fail

2. OpenAI Method
Pros:

Produces idiomatic Python code
Handles modern JavaScript (ES6+)
Better code quality and readability
Understands context and intent

Cons:

Requires API key and internet connection
Costs money per conversion
Rate limits apply
May not be 100% accurate

3. Simple Method
Pros:

Fast and lightweight
No dependencies
Works offline
Free

Cons:

Limited feature support
Only handles basic syntax
May produce incorrect code for complex cases

Example Conversion
JavaScript Input:
function calculateSum(numbers) {
    let total = 0;
    for (let i = 0; i < numbers.length; i++) {
        total += numbers[i];
    }
    console.log("Total:", total);
    return total;
}

const nums = [1][2][3][4][5];
let result = calculateSum(nums);

Python Output (OpenAI method):
def calculate_sum(numbers):
    total = 0
    for i in range(len(numbers)):
        total += numbers[i]
    print("Total:", total)
    return total

nums = [1][2][3][4][5]
result = calculate_sum(nums)

Installation Requirements
# For js2py method
pip install js2py

# For OpenAI method
pip install openai

# Simple method requires no dependencies

Limitations

js2py: Doesn't support ES6+ features, some edge cases may fail
OpenAI: Requires internet, costs money, may have rate limits
Simple: Only handles basic syntax transformations

For production use, consider using js2py for reliability or OpenAI for code quality.Fa

"""

#!/data/data/com.termux/files/usr/bin/env python3
import os
import ast
import multiprocessing
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tspython

# Initialize Tree-Sitter
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

# Define the patterns
# Matches any comment, or a string that is the only child of an expression statement
QUERY_STRING = """
(comment) @comment

(block
  (expression_statement
    (string)) @docstring)

(module
  (expression_statement
    (string)) @docstring)
"""

# Create the Query and Cursor objects
query = Query(PY_LANGUAGE, QUERY_STRING)
cursor = QueryCursor()

def should_preserve_comment(content):
    content = content.strip()
    return any(content.startswith(p) for p in ['#!', '# type:', '# fmt:'])

def strip_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        source_bytes = bytes(source_code, "utf8")
        tree = parser.parse(source_bytes)
        
        # Use the cursor to find matches
        # matches() returns a generator of (match, captures)
        captures = cursor.captures(query, tree.root_node)
        
        modifications = []

        for node, tag in captures:
            if tag == "comment":
                comment_text = source_code[node.start_byte:node.end_byte]
                if not should_preserve_comment(comment_text):
                    modifications.append((node.start_byte, node.end_byte, ""))
            
            elif tag == "docstring":
                # Ensure it's not a standalone string in the middle of a block
                parent = node.parent
                if parent and parent.named_child_count == 1:
                    modifications.append((node.start_byte, node.end_byte, "pass"))
                else:
                    modifications.append((node.start_byte, node.end_byte, ""))

        if not modifications:
            return

        # Sort reverse by start_byte to maintain index validity during string slicing
        modifications.sort(key=lambda x: x[0], reverse=True)
        
        working_code = source_code
        for start, end, replacement in modifications:
            working_code = working_code[:start] + replacement + working_code[end:]

        # AST Validation
        try:
            ast.parse(working_code)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(working_code)
        except SyntaxError:
            # If the strip breaks the code (e.g. indentation issues), skip it
            pass

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    files = [os.path.join(r, f) for r, _, fs in os.walk(".") for f in fs if f.endswith(".py")]
    
    if not files:
        return

    print(f"Processing {len(files)} files using QueryCursor...")
    # Using 'spawn' context is safer for C-extension based libraries in MP
    with multiprocessing.get_context("spawn").Pool() as pool:
        pool.map(strip_file, files)
    print("In-place cleanup complete.")

if __name__ == "__main__":
    main()
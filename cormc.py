#!/usr/bin/env python3
"""
Remove comments and docstrings from Python files recursively using tree-sitter.

Preserves:
- Type comments (# type: ...)
- Formatter directives (# fmt: ...)
- Shebangs (#!)

Uses multiprocessing for speed and updates files in-place without backups.
"""

import sys
import os
import glob
import logging
from pathlib import Path
from multiprocessing import Pool, cpu_count
from typing import Optional, List, Tuple

try:
    from tree_sitter import Language, Parser
    from tree_sitter_languages import get_language, get_parser
except ImportError:
    print("Error: tree-sitter dependencies not installed.", file=sys.stderr)
    print("Install with: pip install tree-sitter tree-sitter-languages", file=sys.stderr)
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CommentRemover:
    """Remove comments and docstrings from Python source code using tree-sitter."""
    
    PRESERVE_PATTERNS = [
        'type:',      # Type comments
        'fmt:',       # Formatter directives
        'noqa',       # NoQA comments
        'pylint:',    # Pylint directives
        'flake8:',    # Flake8 directives
        'mypy:',      # MyPy directives
    ]
    
    def __init__(self):
        """Initialize the parser and language."""
        try:
            self.language = get_language("python")
            self.parser = get_parser("python")
        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter: {e}")
            raise
    
    def should_preserve_comment(self, comment_text: str) -> bool:
        """Check if a comment should be preserved."""
        comment_text = comment_text.strip()
        
        # Always preserve shebangs
        if comment_text.startswith('#!'):
            return True
        
        # Preserve special comments
        for pattern in self.PRESERVE_PATTERNS:
            if pattern in comment_text:
                return True
        
        return False
    
    def parse_file(self, filepath: str) -> Optional[Tuple[str, List[dict]]]:
        """Parse a Python file and return source and comments/docstrings to remove."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                source_code = f.read()
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return None
        
        try:
            tree = self.parser.parse(source_code.encode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to parse {filepath}: {e}")
            return None
        
        return source_code, tree
    
    def extract_removable_ranges(self, source_code: str, tree) -> List[Tuple[int, int]]:
        """Extract byte ranges of comments and docstrings to remove."""
        lines = source_code.split('\n')
        removable_ranges = []
        
        # Process comments
        for line_idx, line in enumerate(lines):
            if '#' not in line:
                continue
            
            comment_start = line.find('#')
            if comment_start == -1:
                continue
            
            # Check if it's inside a string
            if self._is_in_string(line, comment_start):
                continue
            
            comment_text = line[comment_start:]
            
            # Skip if it should be preserved
            if self.should_preserve_comment(comment_text):
                continue
            
            # Calculate byte offset
            byte_offset = sum(len(l.encode('utf-8')) + 1 for l in lines[:line_idx])
            byte_offset += len(line[:comment_start].encode('utf-8'))
            end_offset = byte_offset + len(comment_text.encode('utf-8'))
            
            removable_ranges.append((byte_offset, end_offset))
        
        # Process docstrings
        removable_ranges.extend(self._extract_docstrings(source_code.encode('utf-8'), tree))
        
        # Sort and merge overlapping ranges
        return self._merge_ranges(sorted(removable_ranges))
    
    def _is_in_string(self, line: str, pos: int) -> bool:
        """Check if a position is inside a string literal."""
        in_single = False
        in_double = False
        i = 0
        
        while i < pos:
            if line[i] == "'" and (i == 0 or line[i-1] != '\\'):
                in_single = not in_single
            elif line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                in_double = not in_double
            i += 1
        
        return in_single or in_double
    
    def _extract_docstrings(self, source_bytes: bytes, tree) -> List[Tuple[int, int]]:
        """Extract byte ranges of docstrings."""
        docstring_ranges = []
        
        def walk_tree(node, parent_type=None):
            # Check for string nodes that are docstrings
            if node.type == 'string':
                # A docstring is a string that is the first statement in a function/class/module
                if parent_type in ('function_definition', 'class_definition', 'module'):
                    docstring_ranges.append((node.start_byte, node.end_byte))
            
            for child in node.children:
                # Track if this is a function or class for docstring detection
                child_parent = child.type if child.type in ('function_definition', 'class_definition') else parent_type
                walk_tree(child, child_parent)
        
        walk_tree(tree.root_node)
        return docstring_ranges
    
    def _merge_ranges(self, ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Merge overlapping byte ranges."""
        if not ranges:
            return []
        
        merged = [ranges[0]]
        
        for current_start, current_end in ranges[1:]:
            last_start, last_end = merged[-1]
            
            if current_start <= last_end:
                # Overlapping or adjacent, merge
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                # Non-overlapping, add new range
                merged.append((current_start, current_end))
        
        return merged
    
    def remove_comments_and_docstrings(self, source_code: str, tree) -> str:
        """Remove comments and docstrings from source code."""
        removable_ranges = self.extract_removable_ranges(source_code, tree)
        
        if not removable_ranges:
            return source_code
        
        source_bytes = source_code.encode('utf-8')
        result_bytes = bytearray()
        last_end = 0
        
        for start, end in removable_ranges:
            # Add content before this range
            result_bytes.extend(source_bytes[last_end:start])
            last_end = end
        
        # Add remaining content
        result_bytes.extend(source_bytes[last_end:])
        
        return result_bytes.decode('utf-8', errors='replace')
    
    def process_file(self, filepath: str) -> bool:
        """Process a single Python file."""
        try:
            parsed = self.parse_file(filepath)
            if parsed is None:
                return False
            
            source_code, tree = parsed
            cleaned_code = self.remove_comments_and_docstrings(source_code, tree)
            
            # Write back to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_code)
            
            logger.info(f"Processed: {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")
            return False


def find_python_files(root_dir: str = '.') -> List[str]:
    """Recursively find all Python files in a directory."""
    python_files = []
    
    for py_file in glob.glob(os.path.join(root_dir, '**', '*.py'), recursive=True):
        # Skip common directories
        if any(part in py_file for part in ['__pycache__', '.git', '.venv', 'venv', '.tox']):
            continue
        python_files.append(py_file)
    
    return python_files


def process_files_mp(files: List[str], num_workers: Optional[int] = None) -> Tuple[int, int]:
    """Process files using multiprocessing."""
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)
    
    logger.info(f"Processing {len(files)} files with {num_workers} workers")
    
    remover = CommentRemover()
    
    with Pool(num_workers) as pool:
        results = pool.map(remover.process_file, files)
    
    successful = sum(1 for r in results if r)
    failed = len(results) - successful
    
    return successful, failed


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Remove comments and docstrings from Python files recursively using tree-sitter.'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to process (default: current directory)'
    )
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=None,
        help=f'Number of worker processes (default: {max(1, cpu_count() - 1)})'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Validate directory
    if not os.path.isdir(args.directory):
        logger.error(f"Directory not found: {args.directory}")
        sys.exit(1)
    
    # Find Python files
    python_files = find_python_files(args.directory)
    
    if not python_files:
        logger.warning(f"No Python files found in {args.directory}")
        sys.exit(0)
    
    logger.info(f"Found {len(python_files)} Python files")
    
    # Process files
    successful, failed = process_files_mp(python_files, args.workers)
    
    logger.info(f"Completed: {successful} successful, {failed} failed")
    
    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
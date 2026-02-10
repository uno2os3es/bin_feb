#!/usr/bin/env python3
import re
import mmap
from pathlib import Path
from multiprocessing import Pool, cpu_count
from typing import List

# -------- CONFIG --------
LOG_EXT = ".log"
MMAP_THRESHOLD = 5 * 1024 * 1024  # 5 MB
NUM_WORKERS = cpu_count()  # Use all available CPU cores
# ------------------------

# Patterns to remove
PATTERNS = [
    r'\^\[',           # ^[
    r'\[[\dA-Z;]+m',   # ANSI color codes like [0m, [31m, etc.
    r'\[\d+[A-Z]',     # Cursor movement like [1A, [2B, etc.
    r'\[[\dA-Z;]+',    # Other bracket sequences
    r'\^M',            # Carriage return marker
    r'\(B',            # Character set sequences
    r'\(0',            # Character set sequences
    r'\x1b\[[0-9;]*[A-Za-z]',  # ANSI escape sequences
    r'\x1b\([0-9AB]',  # Character set escape sequences
    r'\r',             # Actual carriage returns
    r'\x0f',           # Shift In (SI)
    r'\x0e',           # Shift Out (SO)
]

# Compile patterns for better performance
COMPILED_PATTERNS = [re.compile(pattern) for pattern in PATTERNS]


def clean_line(line: str) -> str:
    """Remove terminal control sequences from a line."""
    cleaned = line
    
    # Apply all compiled patterns
    for pattern in COMPILED_PATTERNS:
        cleaned = pattern.sub('', cleaned)
    
    # Remove multiple consecutive spaces (optional)
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    
    return cleaned


def clean_file_small(file_path: Path) -> tuple:
    """Clean a small file using regular file I/O."""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Clean each line
        cleaned_lines = [clean_line(line) for line in lines]
        
        # Write back to the same file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
        
        return (file_path, True, "small file")
        
    except Exception as e:
        return (file_path, False, str(e))


def clean_file_large(file_path: Path) -> tuple:
    """Clean a large file using mmap for better performance."""
    try:
        # Read using mmap
        with open(file_path, 'r+b') as f:
            # Get file size
            file_size = f.seek(0, 2)
            f.seek(0)
            
            if file_size == 0:
                return (file_path, True, "empty file")
            
            # Memory-map the file
            with mmap.mmap(f.fileno(), 0) as mmapped_file:
                # Read content
                content = mmapped_file.read().decode('utf-8', errors='ignore')
        
        # Split into lines and clean
        lines = content.splitlines(keepends=True)
        cleaned_lines = [clean_line(line) for line in lines]
        cleaned_content = ''.join(cleaned_lines)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        return (file_path, True, "large file (mmap)")
        
    except Exception as e:
        return (file_path, False, str(e))


def clean_file_worker(file_path: Path) -> tuple:
    """Worker function to clean a single file."""
    try:
        file_size = file_path.stat().st_size
        
        if file_size > MMAP_THRESHOLD:
            return clean_file_large(file_path)
        else:
            return clean_file_small(file_path)
            
    except Exception as e:
        return (file_path, False, str(e))


def main():
    cwd = Path.cwd()
    
    # Find all .log files recursively
    log_files = list(cwd.rglob(f"*{LOG_EXT}"))
    
    if not log_files:
        print(f"No {LOG_EXT} files found.")
        return
    
    print(f"Found {len(log_files)} log file(s).")
    print(f"Using {NUM_WORKERS} worker(s).")
    print(f"Files larger than {MMAP_THRESHOLD / (1024*1024):.1f} MB will use mmap.\n")
    print("Cleaning...\n")
    
    # Process files in parallel
    with Pool(processes=NUM_WORKERS) as pool:
        results = pool.map(clean_file_worker, log_files)
    
    # Print results
    success_count = 0
    error_count = 0
    
    for file_path, success, message in results:
        if success:
            print(f"✓ Cleaned: {file_path} ({message})")
            success_count += 1
        else:
            print(f"✗ Error: {file_path} - {message}")
            error_count += 1
    
    print(f"\nDone. Successfully processed {success_count}/{len(log_files)} file(s).")
    if error_count > 0:
        print(f"Failed: {error_count} file(s).")


if __name__ == "__main__":
    main()

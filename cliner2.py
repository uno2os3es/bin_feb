#!/usr/bin/env python3
import re
from pathlib import Path

# -------- CONFIG --------
LOG_EXT = ".log"
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

def clean_line(line: str) -> str:
    """Remove terminal control sequences from a line."""
    cleaned = line
    
    # Apply all patterns
    for pattern in PATTERNS:
        cleaned = re.sub(pattern, '', cleaned)
    
    # Remove multiple consecutive spaces (optional)
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    
    return cleaned

def clean_file(file_path: Path) -> None:
    """Clean a single log file in place."""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Clean each line
        cleaned_lines = [clean_line(line) for line in lines]
        
        # Write back to the same file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
        
        print(f"✓ Cleaned: {file_path}")
        
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")

def main():
    cwd = Path.cwd()
    
    # Find all .log files recursively
    log_files = list(cwd.rglob(f"*{LOG_EXT}"))
    
    if not log_files:
        print(f"No {LOG_EXT} files found.")
        return
    
    print(f"Found {len(log_files)} log file(s). Cleaning...\n")
    
    for log_file in log_files:
        clean_file(log_file)
    
    print(f"\nDone. Processed {len(log_files)} file(s).")

if __name__ == "__main__":
    main()

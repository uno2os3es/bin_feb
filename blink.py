#!/data/data/com.termux/files/usr/bin/env python3
import os

# Get the current directory
current_dir = os.getcwd()

# Walk through the directory recursively
for root, _dirs, files in os.walk(current_dir):
    for file in files:
        file_path = os.path.join(root, file)
        # Check if it's a symbolic link
        if os.path.islink(file_path):
            # Check if the symbolic link is broken (target doesn't exist)
            if not os.path.exists(file_path):
                try:
                    # Delete the broken link
                    os.remove(file_path)
                    print(f"Deleted broken link: {os.path.relpath(file_path)}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

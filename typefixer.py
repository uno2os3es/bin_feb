#!/data/data/com.termux/files/usr/bin/env python3
import magic

# NOTE: This script requires the 'python-magic' library.
# Install it using: pip install python-magic
# A robust mapping of common MIME types to their preferred file extensions.
# This list can be expanded as needed.
MIME_TO_EXT_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "application/pdf": "pdf",
    "application/zip": "zip",
    "application/x-tar": "tar",
    "video/mp4": "mp4",
    "audio/mpeg": "mp3",
    "text/plain": "txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/octet-stream": None,  # Binary/unknown, skip renaming
}


def get_ext_from_mime(mime_type):
    """Maps a full MIME type string to a standard file extension."""
    # Handle common variants, especially for older JPEGs
    if "image/jpeg" in mime_type:
        return "jpg"
    # Handle text files, which might have many character set variations
    if "text/" in mime_type:
        return "txt"
    # Look up in the specific map
    return MIME_TO_EXT_MAP.get(mime_type.split(";")[0].strip().lower())


def correct_file_extensions(root_dir=".", dry_run=True) -> None:
    """Scans a directory recursively, checks for file extension mismatches using
    libmagic (python-magic), and renames the files in-place if a mismatch is found.

    Args:
        root_dir (str): The starting directory for the recursive scan.
        dry_run (bool): If True, only prints the planned renames without executing them.

    """
    if dry_run:
        pass
    renames_count = 0
    # Create a magic object for efficiency
    m = magic.Magic(mime=True)
    # Walk through the directory structure recursively
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            current_path = Path(dirpath) / filename
            # Skip directories or non-regular files
            if not current_path.is_file():
                continue
            try:
                # 1. Determine the MIME type using libmagic (from content)
                mime_type_full = m.from_file(str(current_path))
                # 2. Convert MIME type to a standard extension
                detected_ext = get_ext_from_mime(mime_type_full)
                if detected_ext is None:
                    # Type is unknown, binary, or explicitly set to skip
                    continue
                # 3. Get the current extension
                current_ext = current_path.suffix.lstrip(".")
                # Check for mismatch (case-insensitive)
                if current_ext.lower() != detected_ext.lower():
                    # Mismatch found!
                    new_filename = f"{current_path.stem}.{detected_ext}"
                    new_path = current_path.with_name(new_filename)
                    if not dry_run:
                        # 4. Perform the rename operation
                        if not new_path.exists():
                            current_path.rename(new_path)
                            renames_count += 1
            except magic.MagicException:
                pass
            except Exception:
                pass
    if dry_run:
        pass


if __name__ == "__main__":
    # --- SAFETY FIRST: RUNS IN DRY RUN MODE BY DEFAULT ---
    correct_file_extensions(root_dir=".", dry_run=False)
    # To run for real, uncomment the line below and comment out the line above:
    # correct_file_extensions(root_dir='.', dry_run=False)

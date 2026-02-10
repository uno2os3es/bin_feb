#!/data/data/com.termux/files/usr/bin/python

import magic
from dh import MIME_TO_EXT


def get_ext_from_mime(mime_type):
    """Maps a full MIME type string to a standard file extension."""
    # Handle common variants, especially for older JPEGs
    if "image/jpeg" in mime_type:
        return "jpg"
    # Handle text files, which might have many character set variations
    if "text/" in mime_type:
        return "txt"
    # Look up in the specific map
    return MIME_TO_EXT.get(mime_type.split(";")[0].strip().lower())


def correct_file_extensions(root_dir=".", dry_run=True) -> None:
    if dry_run:
        pass
    renames_count = 0
    m = magic.Magic(mime=True)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            current_path = Path(dirpath) / filename
            if not current_path.is_file():
                continue
            if current_path.suffix=="css":
                continue
            try:
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
    correct_file_extensions(root_dir=".", dry_run=False)
    # correct_file_extensions(root_dir='.', dry_run=False)

#!/data/data/com.termux/files/usr/bin/python
import os
import stat
from pathlib import Path

import fastwalk


def get_mode(path: Path) -> int:
    """
    Return permission bits only (e.g. 0o775, 0o664),
    stripping file type flags.
    """
    return stat.S_IMODE(path.stat().st_mode)


def normalize_permissions(homedir: str) -> None:
    # Desired permissions
    DIR_PERM = 0o775  # rwxrwxr-x
    FILE_PERM = 0o664  # rw-rw-r--

    for pth in fastwalk.walk(homedir):
        path = Path(pth)
        try:
            current_perm = get_mode(path)
            if path.is_dir():
                if current_perm != DIR_PERM:
                    os.chmod(path, DIR_PERM)
                    print(f"Set permissions for directory: {path} from {oct(current_perm)} to {oct(DIR_PERM)}")

            elif path.is_file():
                if current_perm != FILE_PERM:
                    os.chmod(path, FILE_PERM)
                    print(f"Set permissions for file: {path} from {oct(current_perm)} to {oct(FILE_PERM)}")
                try:
                    for encod in [
                        "utf-8",
                        "windows-1251",
                    ]:
                        with open(
                            path,
                            errors="ignore",
                            encoding=encod,
                        ) as f:
                            h10 = f.read()
                            print(f"{h10!s}")
                except:
                    pribt(f"error reading {path}")

        except PermissionError as e:
            print(f"Permission denied: {path} ({e})")

        except FileNotFoundError:
            # File may disappear during traversal
            continue

        except OSError as e:
            print(f"OS error on {path}: {e}")


if __name__ == "__main__":
    #    home_dir = os.environ.get("HOME")
    #    if not home_dir:
    #        raise RuntimeError("HOME environment variable not set")
    normalize_permissions(".")

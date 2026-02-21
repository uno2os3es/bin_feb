#!/data/data/com.termux/files/usr/bin/env python3
from pathlib import Path
from sys import argv
import tarfile
import zipfile

from dh import unique_path
from fastwalk import walk_files


def whl_to_tar_xz(whl_path: Path):
    target = whl_path.with_suffix(".tar.xz")
    if target.exists():
        target = unique_path(target)
    print(f"[WHL → TAR.XZ] {whl_path.name}")
    try:
        with zipfile.ZipFile(whl_path, "r") as zf, tarfile.open(target, "w:xz") as tf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                with zf.open(member) as source:
                    tarinfo = tarfile.TarInfo(name=member.filename)
                    tarinfo.size = member.file_size
                    tf.addfile(tarinfo, source)
        print(f"[OK] Created {target.name}")
        whl_path.unlink()
    except Exception as e:
        print(f"[ERROR] {whl_path.name}: {e}")


def tar_xz_to_whl(tar_path: Path):
    target = tar_path.with_suffix(".whl")
    tt = str(target).replace(".tar", "")
    target = Path(tt)
    if target.exists():
        target = unique_path(target)
    print(f"[TAR.XZ → WHL] {tar_path.name}")
    try:
        with tarfile.open(tar_path, "r:xz") as tf, zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for member in tf.getmembers():
                if member.isdir():
                    continue
                extracted = tf.extractfile(member)
                if extracted is None:
                    continue
                zf.writestr(member.name, extracted.read())
        print(f"[OK] Created {target.name}")
        tar_path.unlink()
    except Exception as e:
        print(f"[ERROR] {tar_path.name}: {e}")


def main():
    mode = argv[1]
    dir = Path().cwd()
    for pth in walk_files(dir):
        path = Path(pth)
        if mode == "1" and path.suffix == ".whl":
            whl_to_tar_xz(path)
        elif mode == "2" and ".tar.xz" in path.name:
            tar_xz_to_whl(path)


if __name__ == "__main__":
    main()

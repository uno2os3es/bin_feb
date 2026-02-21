#!/data/data/com.termux/files/usr/bin/env python3
import pathlib
import sysconfig


def is_empty_package(dist_info_path) -> bool:
    record_file = os.path.join(dist_info_path, "RECORD")
    if not pathlib.Path(record_file).is_file():
        return False
    with pathlib.Path(record_file).open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            rel_path = row[0]
            abs_path = pathlib.Path(
                os.path.join(
                    pathlib.Path(dist_info_path).parent,
                    rel_path,
                )
            ).resolve()
            if not abs_path.startswith(pathlib.Path(dist_info_path).resolve() + os.sep):
                return False
    return True


def find_empty_packages(site_packages):
    empty = []
    for entry in os.listdir(site_packages):
        if entry.endswith(".dist-info"):
            dist_info_path = os.path.join(site_packages, entry)
            if is_empty_package(dist_info_path):
                empty.append(dist_info_path)
    return empty


def main() -> None:
    site_packages = sysconfig.get_paths()["purelib"]
    empty = find_empty_packages(site_packages)
    if not empty:
        return
    for _p in empty:
        pass


if __name__ == "__main__":
    main()

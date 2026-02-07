#!/data/data/com.termux/files/usr/bin/env python3
import zipfile


def is_empty_wheel(wheel_path) -> bool:
    """Return True if all files recorded in RECORD are inside the dist-info dir."""
    with zipfile.ZipFile(wheel_path, "r") as z:
        # Find the dist-info directory inside the wheel
        dist_info_dirs = [name for name in z.namelist() if name.endswith((".dist-info/", ".dist-info"))]
        if not dist_info_dirs:
            return False  # malformed wheel; no dist-info
        # Use the first (there should only be one)
        dist_info = dist_info_dirs[0].rstrip("/")
        # Location of RECORD file
        record_path = dist_info + "/RECORD"
        if record_path not in z.namelist():
            return False  # malformed; no RECORD → assume not empty
        # Read RECORD CSV
        with z.open(record_path) as f:
            reader = csv.reader(line.decode("utf-8") for line in f)
            for row in reader:
                if not row:
                    continue
                file_path = row[0]
                # Wheel RECORD entries are relative paths
                # Check whether the file is inside the dist-info directory
                if not file_path.startswith(dist_info + "/"):
                    return False  # file exists outside dist-info → not empty
    return True


def main() -> None:
    wheels = [f for f in os.listdir(".") if f.endswith(".whl")]
    if not wheels:
        return
    empty = [wheel for wheel in wheels if is_empty_wheel(wheel)]
    if not empty:
        return
    for _w in empty:
        pass


if __name__ == "__main__":
    main()

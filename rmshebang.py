#!/data/data/com.termux/files/usr/bin/env python3
TARGET_STR = "#!/data/data/com.termux/files/usr/bin/env python3"


def is_text_file(filepath) -> bool | None:
    try:
        with Path(filepath).open("r", encoding="utf-8") as f:
            f.read()
        return True
    except (UnicodeDecodeError, PermissionError):
        return False


def process_file(filepath) -> None:
    try:
        with Path(filepath).open("r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = [line for line in lines if TARGET_STR not in line]
        if len(new_lines) != len(lines):
            with Path(filepath).open("w", encoding="utf-8") as f:
                f.writelines(new_lines)
    except Exception:
        pass


def main() -> None:
    for root, _dirs, files in os.walk("."):
        for file in files:
            if file in {"rmshebang", "socket"}:
                continue
            if file.endswith((".body", ".rs")):
                continue
            if file.endswith((".js", ".json")):
                continue
            if file.endswith((".css", ".html")):
                continue
            if file.endswith((".jpg", ".png")):
                continue
            if file.endswith((".ttf", ".eot")):
                continue
            if file.endswith((".md", ".txt")):
                continue
            if file.endswith((".woff", ".woff2")):
                continue
            filepath = os.path.join(root, file)
            if not Path(filepath).exists():
                continue
            if is_text_file(filepath):
                process_file(filepath)


if __name__ == "__main__":
    main()

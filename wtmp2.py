#!/data/data/com.termux/files/usr/bin/env python3
import os
import shutil
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

DEST_DIR = os.path.expanduser("~/tmp/temp")


def copy_if_match(src_path) -> bool:
    if str(src_path).endswith("robots.txt.tmp"):
        return False
    try:
        os.makedirs(DEST_DIR, exist_ok=True)
        dest = os.path.join(
            DEST_DIR,
            os.path.basename(src_path),
        )
        if os.path.exists(src_path):
            shutil.copy2(src_path, dest)
            print(src_path)
            return True
        else:
            print("file not found.")
            return False
    except Exception as e:
        return f"Error copying file : {e}"
    return False


class CopyEventHandler(FileSystemEventHandler):
    def on_created(self, event) -> None:
        if not event.is_directory:
            copy_if_match(event.src_path)

    def on_modified(self, event) -> None:
        if not event.is_directory:
            copy_if_match(event.src_path)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    event_handler = CopyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(0.0001)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

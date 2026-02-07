#!/data/data/com.termux/files/usr/bin/env python3
# import the modules
import logging
import sys
import time

from watchdog.events import LoggingEventHandler
from watchdog.observers import Observer

if __name__ == "__main__":
    # Set the format for logging info
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set format for displaying path
    path = sys.argv[1] if len(sys.argv) > 1 else "."

    # Initialize logging event handler
    event_handler = LoggingEventHandler()

    # Initialize Observer
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)

    # Start the observer
    observer.start()
    try:
        while True:
            # Set the thread sleep time
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

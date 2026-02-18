#!/data/data/com.termux/files/usr/bin/env python3
import pathlib
import sys
from multiprocessing import Process, Queue, cpu_count

import cv2
import pytesseract
from PIL import Image
from termcolor import cprint

video = sys.argv[1]
txtfile = pathlib.Path(video).with_suffix(".txt")


def ocr_worker(q_in: Queue, q_out: Queue):
    while True:
        item = q_in.get()
        if item is None:
            break
        frame_id, frame = item
        frame = cv2.resize(frame, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(Image.fromarray(gray), lang="eng", config="--oem 1 --psm 6")
        if text and len(text.strip()) > 5:
            cprint(f"frame {frame_id} --> {text}", "cyan")
            txtfile.open("a", encoding="utf-8").write(text + "\n")
        else:
            cprint(f"frame {frame_id} --> no text", "blue")
        q_out.put((frame_id, text))


def main():
    cap = cv2.VideoCapture(video)

    q_in = Queue(maxsize=cpu_count() * 2)
    q_out = Queue()

    workers = [Process(target=ocr_worker, args=(q_in, q_out)) for _ in range(cpu_count())]

    for w in workers:
        w.start()

    frame_id = 0
    sent = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_id += 1
        if frame_id % 2 == 0:
            q_in.put((frame_id, frame))
            sent += 1

    # stop workers
    for _ in workers:
        q_in.put(None)

    received = 0
    while received < sent:
        _fid, _text = q_out.get()
        received += 1

    cap.release()
    for w in workers:
        w.join()


if __name__ == "__main__":
    main()

#!/data/data/com.termux/files/usr/bin/python
import math
import os
import threading

import requests


class MultiPartDownloader:

    def __init__(self, url, output_path, num_threads=4):
        self.url = url
        self.output_path = output_path
        self.num_threads = num_threads
        self.file_size = 0
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.support_resume = False
        self.existing_size = 0

    def get_file_size(self):
        response = requests.head(self.url,
                                 headers=self.headers,
                                 allow_redirects=True)
        if "Content-Length" in response.headers:
            self.file_size = int(response.headers["Content-Length"])
        if "Accept-Ranges" in response.headers and response.headers[
                "Accept-Ranges"] == "bytes":
            self.support_resume = True
        return self.file_size

    def check_existing_file(self):
        if os.path.exists(self.output_path):
            self.existing_size = os.path.getsize(self.output_path)
            return self.existing_size
        return 0

    def download_range(self, start, end, part_num):
        headers = {"Range": f"bytes={start}-{end}", **self.headers}
        response = requests.get(self.url, headers=headers, stream=True)
        chunk_size = 1024 * 1024  # 1MB per chunk
        with open(self.output_path, "r+b") as f:
            f.seek(start)
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    f.flush()

    def download(self):
        if not self.file_size:
            self.get_file_size()
        if not self.support_resume:
            print(
                "Server does not support resume. Downloading in single part..."
            )
            self.num_threads = 1

        existing_size = self.check_existing_file()
        if existing_size == self.file_size:
            print("File already downloaded.")
            return

        if existing_size > 0 and not self.support_resume:
            print("Cannot resume. Starting from scratch.")
            existing_size = 0

        part_size = math.ceil(
            (self.file_size - existing_size) / self.num_threads)
        threads = []
        for i in range(self.num_threads):
            start = existing_size + i * part_size
            end = min(existing_size + (i + 1) * part_size, self.file_size) - 1
            if start >= self.file_size:
                break
            thread = threading.Thread(target=self.download_range,
                                      args=(start, end, i))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        print("Download completed!")


if __name__ == "__main__":
    url = input("Enter the file URL: ")
    output_path = input("Enter the output file path: ")
    num_threads = int(input("Enter the number of threads (default 4): ") or 8)

    downloader = MultiPartDownloader(url, output_path, num_threads)
    downloader.download()

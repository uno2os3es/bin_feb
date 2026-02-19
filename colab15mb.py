#!/data/data/com.termux/files/usr/bin/env python3
import os
import site
import tarfile

from google.colab import files


def get_folder_size(path):
    """Return total size of a folder in bytes."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total


def compress_small_site_packages(max_size_mb=15):
    site_packages_dir = site.getsitepackages()[0]
    output_file = "site-packages-small.tar.gz"

    with tarfile.open(output_file, "w:gz") as tar:
        for item in os.listdir(site_packages_dir):
            item_path = os.path.join(site_packages_dir, item)

            if os.path.isdir(item_path):
                folder_size_mb = get_folder_size(item_path) / (1024 * 1024)
                if folder_size_mb <= max_size_mb:
                    print(f"Including folder {item} ({folder_size_mb:.2f} MB)")
                    for (
                        root,
                        _dirs,
                        files_list,
                    ) in os.walk(item_path):
                        for f in files_list:
                            if not f.endswith(".pyc"):
                                full_path = os.path.join(root, f)
                                arcname = os.path.relpath(
                                    full_path,
                                    site_packages_dir,
                                )
                                tar.add(
                                    full_path,
                                    arcname=arcname,
                                )

            elif os.path.isfile(item_path):
                file_size_mb = os.path.getsize(item_path) / (1024 * 1024)
                if file_size_mb <= max_size_mb and not item.endswith(".pyc"):
                    print(f"Including file {item} ({file_size_mb:.2f} MB)")
                    arcname = os.path.relpath(
                        item_path,
                        site_packages_dir,
                    )
                    tar.add(item_path, arcname=arcname)

    print(f"Archive created: {output_file}")
    files.download(output_file)


compress_small_site_packages(max_size_mb=15)

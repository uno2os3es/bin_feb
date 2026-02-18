#!/data/data/com.termux/files/usr/bin/env python3
import os
import random
import string
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastwalk import walk_files


def random_key(length=32):
    # AES requires 16, 24, or 32 bytes
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def encrypt_file(file_path, key):
    backend = default_backend()
    iv = os.urandom(16)

    cipher = Cipher(
        algorithms.AES(key.encode()),
        modes.CBC(iv),
        backend=backend,
    )
    encryptor = cipher.encryptor()

    with open(file_path, "rb") as f:
        data = f.read()

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    with open(file_path, "wb") as f:
        # store IV + ciphertext so decryption is possible
        f.write(iv + encrypted_data)


def decrypt_file(file_path, key):
    backend = default_backend()

    with open(file_path, "rb") as f:
        raw = f.read()

    iv = raw[:AES_BLOCK_SIZE]
    ciphertext = raw[AES_BLOCK_SIZE:]

    cipher = Cipher(
        algorithms.AES(key.encode()),
        modes.CBC(iv),
        backend=backend,
    )
    decryptor = cipher.decryptor()

    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()

    with open(file_path, "wb") as f:
        f.write(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--encrypt", action="store_true")
    parser.add_argument("--decrypt", action="store_true")
    parser.add_argument("--key", help="Encryption/decryption key")
    args = parser.parse_args()

    if args.encrypt:
        key = random_key()
        print(f"Encryption key: {key}")
        action = encrypt_file
        with open("key", "a") as f:
            f.write("\n")
            f.write(key)

    elif args.decrypt:
        if not args.key:
            raise SystemExit("Decryption requires --key")
        with open("key") as f:
            key = f.read().strip()
        action = decrypt_file

    else:
        raise SystemExit("Specify --encrypt or --decrypt")

    for file_path in walk_files("."):
        path = Path(file_path)
        if path.exists():
            action(file_path, key)


if __name__ == "__main__":
    main()

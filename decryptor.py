#!/data/data/com.termux/files/usr/bin/python
import argparse
import glob
import os
import random
import string

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

AES_BLOCK_SIZE = 16


def random_key(length=32):
    # AES valid sizes: 16, 24, 32 bytes
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def encrypt_file(file_path, key):
    backend = default_backend()
    iv = os.urandom(AES_BLOCK_SIZE)

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
        # prepend IV so decryption can recover it
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

    elif args.decrypt:
        if not args.key:
            raise SystemExit("Decryption requires --key")
        key = args.key
        action = decrypt_file

    else:
        raise SystemExit("Specify --encrypt or --decrypt")

    for file_path in glob.glob("*"):
        if os.path.isfile(file_path):
            print(f"Processing {file_path}...")
            action(file_path, key)


if __name__ == "__main__":
    main()

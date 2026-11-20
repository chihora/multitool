import hashlib
from pathlib import Path


def hash_text(algorithm: str, text: str) -> str:
    data = text.encode()
    if algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    if algorithm == "md5":
        return hashlib.md5(data, usedforsecurity=False).hexdigest()
    raise ValueError(f"unknown hash algorithm: {algorithm}")


def hash_file(algorithm: str, path: str | Path) -> str:
    if algorithm == "sha256":
        digest = hashlib.sha256()
    elif algorithm == "md5":
        digest = hashlib.md5(usedforsecurity=False)
    else:
        raise ValueError(f"unknown hash algorithm: {algorithm}")

    with Path(path).open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()

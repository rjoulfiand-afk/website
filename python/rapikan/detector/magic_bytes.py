"""Security: file-type detection via magic bytes."""

from __future__ import annotations

from pathlib import Path

# Magic byte signatures for common file types.
# DOCX/XLSX/PPTX are all ZIP-based; we detect via PK header then
# further check internal structure in the converter.
MAGIC_SIGNATURES: dict[str, bytes] = {
    "docx": b"PK\x03\x04",  # ZIP / Office Open XML
    "pdf": b"%PDF",
    "exe": b"MZ",
    "zip": b"PK\x03\x04",
    "rar": b"Rar!",
    "7z": b"7z\xbc\xaf\x27\x1c",
}

# Only these content-types are accepted for processing.
ALLOWED_MAGIC = {b"PK\x03\x04"}  # DOCX must start with ZIP magic


class UnsupportedFileTypeError(ValueError):
    """Raised when a file's magic bytes indicate an unsupported/dangerous type."""


def detect_magic(path: Path, num_bytes: int = 8) -> bytes:
    """Read the first *num_bytes* bytes from *path* and return them."""
    with open(path, "rb") as fh:
        return fh.read(num_bytes)


def assert_is_zip_based(path: Path) -> None:
    """Raise UnsupportedFileTypeError if *path* does not start with PK magic."""
    magic = detect_magic(path, 4)
    if magic[:4] != b"PK\x03\x04":
        raise UnsupportedFileTypeError(
            f"File does not appear to be a ZIP/DOCX (magic={magic!r}): {path}"
        )

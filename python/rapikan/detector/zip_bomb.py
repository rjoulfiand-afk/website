"""Security: ZIP-bomb detection."""

from __future__ import annotations

import zipfile
from pathlib import Path


class ZipBombError(ValueError):
    """Raised when a ZIP archive looks like a zip-bomb."""


def check_zip_safety(
    path: Path,
    max_entries: int = 1000,
    max_ratio: int = 100,
) -> None:
    """Inspect a ZIP file and raise ZipBombError if limits are exceeded.

    Parameters
    ----------
    path:
        Path to the ZIP/DOCX file.
    max_entries:
        Maximum number of entries allowed in the archive.
    max_ratio:
        Maximum allowed ratio of total_uncompressed / total_compressed size.
    """
    with zipfile.ZipFile(path, "r") as zf:
        entries = zf.infolist()

        if len(entries) > max_entries:
            raise ZipBombError(
                f"ZIP has {len(entries)} entries (limit {max_entries}): {path}"
            )

        total_compressed = sum(e.compress_size for e in entries)
        total_uncompressed = sum(e.file_size for e in entries)

        if total_compressed > 0 and (total_uncompressed / total_compressed) > max_ratio:
            raise ZipBombError(
                f"ZIP compression ratio {total_uncompressed/total_compressed:.1f}x "
                f"exceeds limit {max_ratio}x: {path}"
            )

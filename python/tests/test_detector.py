"""Tests for security checks: magic bytes, zip-bomb, and upload safety."""

import io
import zipfile
import pytest
from pathlib import Path
from rapikan.detector.magic_bytes import (
    assert_is_zip_based,
    detect_magic,
    UnsupportedFileTypeError,
)
from rapikan.detector.zip_bomb import check_zip_safety, ZipBombError
from rapikan.config import Settings


def test_magic_bytes_valid_docx(tmp_path: Path):
    """A valid docx starting with PK\\x03\\x04 passes magic byte validation."""
    valid_file = tmp_path / "valid.docx"
    valid_file.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
    assert_is_zip_based(valid_file)
    assert detect_magic(valid_file, 4) == b"PK\x03\x04"


def test_magic_bytes_reject_exe_renamed_to_docx(tmp_path: Path):
    """An executable (MZ magic header) renamed to .docx must be rejected."""
    fake_doc = tmp_path / "malicious.docx"
    # MZ executable header
    fake_doc.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff")
    with pytest.raises(UnsupportedFileTypeError) as exc_info:
        assert_is_zip_based(fake_doc)
    assert "does not appear to be a ZIP/DOCX" in str(exc_info.value)


def test_magic_bytes_reject_pdf(tmp_path: Path):
    """A PDF file renamed to .docx must be rejected by magic bytes."""
    fake_doc = tmp_path / "sample.docx"
    fake_doc.write_bytes(b"%PDF-1.4\n%test")
    with pytest.raises(UnsupportedFileTypeError):
        assert_is_zip_based(fake_doc)


def test_magic_bytes_reject_empty_or_short_file(tmp_path: Path):
    """Empty or very short files cannot be valid ZIP files."""
    short_file = tmp_path / "corrupt.docx"
    short_file.write_bytes(b"PK")
    with pytest.raises(UnsupportedFileTypeError):
        assert_is_zip_based(short_file)


def test_zip_safety_excessive_entries(tmp_path: Path):
    """ZIP with more entries than max_entries must trigger ZipBombError."""
    zip_path = tmp_path / "many_files.docx"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for i in range(25):
            zf.writestr(f"entry_{i}.xml", "test content")

    # With max_entries=20, this should fail
    with pytest.raises(ZipBombError) as exc_info:
        check_zip_safety(zip_path, max_entries=20)
    assert "entries (limit 20)" in str(exc_info.value)


def test_zip_safety_excessive_ratio(tmp_path: Path):
    """ZIP with high compression ratio (e.g. 1000:1) must trigger ZipBombError."""
    zip_path = tmp_path / "ratio_bomb.docx"
    # Write 1MB of zeroes compressed heavily
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("zeroes.xml", b"\x00" * (1024 * 1024))

    # Compression ratio of 1MB zeroes is ~1000x
    with pytest.raises(ZipBombError) as exc_info:
        check_zip_safety(zip_path, max_ratio=20)
    assert "compression ratio" in str(exc_info.value)


def test_zip_safety_normal_archive(tmp_path: Path):
    """Normal docx archive with typical entry count and ratio passes safety check."""
    zip_path = tmp_path / "normal.docx"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "<Types></Types>")
        zf.writestr("word/document.xml", "<w:document><w:body/></w:document>")

    check_zip_safety(zip_path, max_entries=100, max_ratio=50)


def test_file_size_limit_setting():
    """Settings enforces max_file_size_bytes calculation."""
    cfg = Settings(max_file_size_mb=10)
    assert cfg.max_file_size_bytes == 10 * 1024 * 1024

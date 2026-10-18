"""Pytest configuration and programmatic DOCX fixtures for Rapikan tests."""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

# Ensure root of python package is in sys.path
_python_root = Path(__file__).resolve().parent.parent
if str(_python_root) not in sys.path:
    sys.path.insert(0, str(_python_root))
from typing import Generator
import pytest
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH


def create_minimal_theme_xml() -> bytes:
    """Return bytes of a minimal word/theme/theme1.xml with major and minor latin fonts."""
    return b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1F497D"/></a:dk2>
      <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
      <a:accent1><a:srgbClr val="4F81BD"/></a:accent1>
      <a:accent2><a:srgbClr val="C0504D"/></a:accent2>
      <a:accent3><a:srgbClr val="9BBB59"/></a:accent3>
      <a:accent4><a:srgbClr val="8064A2"/></a:accent4>
      <a:accent5><a:srgbClr val="4BACC6"/></a:accent5>
      <a:accent6><a:srgbClr val="F79646"/></a:accent6>
      <a:hlink><a:srgbClr val="0000FF"/></a:hlink>
      <a:folHlink><a:srgbClr val="800080"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont>
        <a:latin typeface="Aptos Display"/>
      </a:majorFont>
      <a:minorFont>
        <a:latin typeface="Aptos"/>
      </a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst/>
      <a:lnStyleLst/>
      <a:effectStyleLst/>
      <a:bgFillStyleLst/>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>"""


def add_theme_to_docx(docx_path: Path, theme_bytes: bytes) -> None:
    """Inject word/theme/theme1.xml and corresponding relationship into docx."""
    # Read existing zip entries
    buffer = io.BytesIO()
    with zipfile.ZipFile(docx_path, "r") as zin:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename != "word/theme/theme1.xml":
                    zout.writestr(item, zin.read(item.filename))
            zout.writestr("word/theme/theme1.xml", theme_bytes)
    docx_path.write_bytes(buffer.getvalue())


@pytest.fixture
def tmp_docx_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary directory for generated DOCX test files."""
    d = tmp_path / "docx_fixtures"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def sample_docx_factory(tmp_docx_dir: Path):
    """Factory fixture to create programmatic docx files with specific XML structures."""

    def _create(
        filename: str = "test.docx",
        with_theme: bool = False,
        with_doc_defaults: bool = False,
    ) -> Path:
        doc = Document()
        path = tmp_docx_dir / filename
        doc.save(str(path))

        if with_theme:
            add_theme_to_docx(path, create_minimal_theme_xml())

        return path

    return _create

"""Tests for DOCX → IR converter.

Covers:
- Font size in half-points (w:sz)
- Line spacing: auto vs exact vs atLeast
- Section margins in twips with rounding tolerance
- Style inheritance (basedOn chain)
- Document defaults (docDefaults)
- Theme fonts (theme1.xml -> asciiTheme)
- Run-level direct formatting overrides and provenance
- Fields (PAGE, TOC, SEQ)
- Section properties (pgNumType, different_first_page)
- Paragraph text_hash and ID generation
"""

import hashlib
from pathlib import Path
import pytest
from docx import Document
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
from docx.shared import Pt, Cm, RGBColor

from rapikan.converter.docx_converter import convert_docx
from rapikan.ir.schema import (
    FieldType,
    LineSpacingRule,
    Provenance,
)
from rapikan.utils.twips import cm_to_twips, twips_approx_equal


def test_font_size_half_points(tmp_path: Path):
    """Ensure w:sz half-point values are converted to standard points (28 -> 14.0 pt)."""
    docx_path = tmp_path / "fontsize.docx"
    doc = Document()
    p = doc.add_paragraph("Heading text with 14pt")
    # Add a run with explicit half-point size via oxml
    run = p.runs[0]
    rPr = run._element.get_or_add_rPr()
    sz = parse_xml(f'<w:sz {nsdecls("w")} w:val="28"/>')
    rPr.append(sz)
    doc.save(str(docx_path))

    ir = convert_docx(docx_path)
    assert len(ir.paragraphs) >= 1
    para = ir.paragraphs[0]
    assert len(para.runs) >= 1
    assert para.runs[0].effective_style.font_size_pt == 14.0


def test_line_spacing_auto_exact_atleast(tmp_path: Path):
    """Test line spacing conversion for auto, exact, and atLeast."""
    docx_path = tmp_path / "spacing.docx"
    doc = Document()

    # Para 1: Auto 240 twips (1.0 line)
    p1 = doc.add_paragraph("Paragraph auto spacing")
    pPr1 = p1._element.get_or_add_pPr()
    sp1 = parse_xml(f'<w:spacing {nsdecls("w")} w:line="240" w:lineRule="auto"/>')
    pPr1.append(sp1)

    # Para 2: Exact 480 twips (24pt)
    p2 = doc.add_paragraph("Paragraph exact spacing 24pt")
    pPr2 = p2._element.get_or_add_pPr()
    sp2 = parse_xml(f'<w:spacing {nsdecls("w")} w:line="480" w:lineRule="exact"/>')
    pPr2.append(sp2)

    # Para 3: AtLeast 360 twips (18pt)
    p3 = doc.add_paragraph("Paragraph atLeast spacing 18pt")
    pPr3 = p3._element.get_or_add_pPr()
    sp3 = parse_xml(f'<w:spacing {nsdecls("w")} w:line="360" w:lineRule="atLeast"/>')
    pPr3.append(sp3)

    doc.save(str(docx_path))

    ir = convert_docx(docx_path)
    assert len(ir.paragraphs) >= 3

    ls1 = ir.paragraphs[0].effective_style.line_spacing
    assert ls1 is not None
    assert ls1.rule == LineSpacingRule.AUTO
    assert ls1.value_pt == 12.0  # 240 twips / 20 = 12pt

    ls2 = ir.paragraphs[1].effective_style.line_spacing
    assert ls2 is not None
    assert ls2.rule == LineSpacingRule.EXACT
    assert ls2.value_pt == 24.0  # 480 twips / 20 = 24pt

    ls3 = ir.paragraphs[2].effective_style.line_spacing
    assert ls3 is not None
    assert ls3.rule == LineSpacingRule.AT_LEAST
    assert ls3.value_pt == 18.0  # 360 twips / 20 = 18pt


def test_margins_in_twips_with_tolerance(tmp_path: Path):
    """Test section margins conversion with 4cm = 2268 twips and 3cm = 1701 twips."""
    docx_path = tmp_path / "margins.docx"
    doc = Document()
    doc.add_paragraph("Document with 4cm top/left and 3cm bottom/right margins.")

    # Apply margins to section
    sect = doc.sections[0]
    sect.top_margin = Cm(4)
    sect.bottom_margin = Cm(3)
    sect.left_margin = Cm(4)
    sect.right_margin = Cm(3)
    doc.save(str(docx_path))

    ir = convert_docx(docx_path)
    assert len(ir.sections) >= 1
    m = ir.sections[0].margins

    # 4cm = ~2268 twips, 3cm = ~1701 twips
    expected_4cm_twips = cm_to_twips(4.0)  # 2268
    expected_3cm_twips = cm_to_twips(3.0)  # 1701

    assert m.top_twip is not None
    assert twips_approx_equal(m.top_twip, expected_4cm_twips, tolerance=5)
    assert twips_approx_equal(m.left_twip, expected_4cm_twips, tolerance=5)
    assert twips_approx_equal(m.bottom_twip, expected_3cm_twips, tolerance=5)
    assert twips_approx_equal(m.right_twip, expected_3cm_twips, tolerance=5)
    assert round(m.top_cm, 1) == 4.0
    assert round(m.left_cm, 1) == 4.0
    assert round(m.bottom_cm, 1) == 3.0
    assert round(m.right_cm, 1) == 3.0


def test_based_on_style_inheritance_chain(tmp_path: Path):
    """Test basedOn style inheritance resolution across multiple levels."""
    docx_path = tmp_path / "basedon.docx"
    doc = Document()

    # Modify styles element directly
    styles_elm = doc.part.styles.element
    # Create BaseStyle: bold, Times New Roman, 12pt
    base_style_xml = parse_xml(f'''
        <w:style {nsdecls("w")} w:type="paragraph" w:styleId="BaseStyle">
            <w:name w:val="BaseStyle"/>
            <w:rPr>
                <w:rFonts w:ascii="Times New Roman"/>
                <w:b/>
                <w:sz w:val="24"/>
            </w:rPr>
        </w:style>
    ''')
    # Create DerivedStyle basedOn BaseStyle: overrides sz to 28 (14pt), adds italic
    derived_style_xml = parse_xml(f'''
        <w:style {nsdecls("w")} w:type="paragraph" w:styleId="DerivedStyle">
            <w:name w:val="DerivedStyle"/>
            <w:basedOn w:val="BaseStyle"/>
            <w:rPr>
                <w:i/>
                <w:sz w:val="28"/>
            </w:rPr>
        </w:style>
    ''')
    styles_elm.append(base_style_xml)
    styles_elm.append(derived_style_xml)

    p = doc.add_paragraph("Text with derived style")
    pPr = p._element.get_or_add_pPr()
    pPr.append(parse_xml(f'<w:pStyle {nsdecls("w")} w:val="DerivedStyle"/>'))

    doc.save(str(docx_path))

    ir = convert_docx(docx_path)
    para = ir.paragraphs[0]

    # Should inherit font_name="Times New Roman" and bold=True from BaseStyle,
    # and get font_size_pt=14.0 and italic=True from DerivedStyle
    assert para.effective_style.font_name == "Times New Roman"
    assert para.effective_style.bold is True
    assert para.effective_style.italic is True
    assert para.effective_style.font_size_pt == 14.0


def test_doc_defaults_and_provenance(tmp_path: Path):
    """Test document defaults in styles.xml and provenance assignment."""
    docx_path = tmp_path / "docdefaults.docx"
    doc = Document()

    # Inject docDefaults into styles
    styles_elm = doc.part.styles.element
    existing_dd = styles_elm.find(qn("w:docDefaults"))
    if existing_dd is not None:
        styles_elm.remove(existing_dd)

    dd_xml = parse_xml(f'''
        <w:docDefaults {nsdecls("w")}>
            <w:rPrDefault>
                <w:rPr>
                    <w:rFonts w:ascii="Georgia"/>
                    <w:sz w:val="22"/>
                </w:rPr>
            </w:rPrDefault>
        </w:docDefaults>
    ''')
    styles_elm.insert(0, dd_xml)

    doc.add_paragraph("Paragraph with default font")
    doc.save(str(docx_path))

    ir = convert_docx(docx_path)
    para = ir.paragraphs[0]
    assert para.effective_style.font_name == "Georgia"
    assert para.effective_style.font_size_pt == 11.0  # 22 / 2
    assert para.provenance.font_name == Provenance.DOC_DEFAULT


def test_theme_font_resolution(tmp_path: Path, sample_docx_factory):
    """Test resolution of theme fonts from word/theme/theme1.xml."""
    docx_path = sample_docx_factory("themed.docx", with_theme=True)
    doc = Document(str(docx_path))

    p = doc.add_paragraph("Theme Font Paragraph")
    run = p.runs[0]
    rPr = run._element.get_or_add_rPr()
    rPr.append(parse_xml(f'<w:rFonts {nsdecls("w")} w:asciiTheme="majorHAnsi"/>'))
    doc.save(str(docx_path))

    ir = convert_docx(docx_path)
    assert ir.theme.major_font == "Aptos Display"
    assert ir.theme.minor_font == "Aptos"
    para = ir.paragraphs[0]
    assert para.runs[0].effective_style.font_name == "Aptos Display"


def test_direct_formatting_override_on_run(tmp_path: Path):
    """Test direct formatting on a run overrides paragraph style with provenance tracking."""
    docx_path = tmp_path / "run_override.docx"
    doc = Document()
    p = doc.add_paragraph("Plain text and ")
    bold_run = p.add_run("BOLD RED TEXT")
    bold_run.bold = True
    bold_run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
    doc.save(str(docx_path))

    ir = convert_docx(docx_path)
    para = ir.paragraphs[0]
    assert len(para.runs) == 2

    run2 = para.runs[1]
    assert run2.text == "BOLD RED TEXT"
    assert run2.effective_style.bold is True
    assert run2.provenance["bold"] == Provenance.DIRECT


def test_fields_parsing_page_and_toc(tmp_path: Path):
    """Test detection and parsing of PAGE, TOC, and SEQ fields."""
    docx_path = tmp_path / "fields.docx"
    doc = Document()

    # Paragraph with PAGE field
    p1 = doc.add_paragraph("Page number: ")
    fld = parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr="PAGE"/>')
    p1._element.append(fld)

    # Paragraph with complex TOC field
    p2 = doc.add_paragraph()
    fld_begin = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    instr = parse_xml(f'<w:instrText {nsdecls("w")}>TOC \\o "1-3" \\h \\z</w:instrText>')
    fld_end = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
    p2._element.append(fld_begin)
    p2._element.append(instr)
    p2._element.append(fld_end)

    doc.save(str(docx_path))

    ir = convert_docx(docx_path)
    assert len(ir.paragraphs[0].fields) == 1
    assert ir.paragraphs[0].fields[0].field_type == FieldType.PAGE

    assert len(ir.paragraphs[1].fields) == 1
    assert ir.paragraphs[1].fields[0].field_type == FieldType.TOC
    assert ir.toc.is_auto is True


def test_paragraph_id_and_text_hash(tmp_path: Path):
    """Test that all paragraphs have deterministic p_0001 IDs and correct SHA-256 text_hash."""
    docx_path = tmp_path / "ids.docx"
    doc = Document()
    doc.add_paragraph("First paragraph.")
    doc.add_paragraph("Second paragraph.")
    doc.save(str(docx_path))

    ir = convert_docx(docx_path)
    assert ir.paragraphs[0].id == "p_0001"
    assert ir.paragraphs[1].id == "p_0002"

    expected_hash_0 = hashlib.sha256("First paragraph.".encode("utf-8")).hexdigest()
    expected_hash_1 = hashlib.sha256("Second paragraph.".encode("utf-8")).hexdigest()

    assert ir.paragraphs[0].text_hash == expected_hash_0
    assert ir.paragraphs[1].text_hash == expected_hash_1

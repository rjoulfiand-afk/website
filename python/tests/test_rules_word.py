"""Tests for Word and Cross-Section deterministic rules (Phase 1).

Covers:
- W001: Fake Heading
- W002: Manual Numbering
- W003: Font Mix within paragraph
- W004: Inconsistent Margins across sections
- W005: TOC missing or stale / not auto
- W006: Table missing formatted header row
- W007: Missing captions for tables/figures
- W008: Manual spacing (consecutive blank paragraphs)
- W010: Double spaces
- W012: Chapter order violation
- X001: Citation without bibliography entry
- X002: Bibliography entry not cited in body
- X003: TOC entry != actual heading
- X004: Sequence numbering gaps / out of order
- B002: Common Indonesian typos / non-standard words
"""

import pytest
from rapikan.ir.schema import (
    BibEntry,
    Caption,
    Cell,
    CellAddress,
    EffectiveStyle,
    IRDocument,
    InlineCitation,
    Paragraph,
    Row,
    Run,
    RunStyle,
    Section,
    SectionMargins,
    Table,
    TOCBlock,
    TOCEntry,
)
from rapikan.rules.campus_profile import CampusProfile, DEFAULT_PROFILE
from rapikan.rules.word.W001_fake_heading import W001FakeHeading
from rapikan.rules.word.W002_manual_numbering import W002ManualNumbering
from rapikan.rules.word.W003_font_mix import W003FontMix
from rapikan.rules.word.W004_margin_section import W004MarginSection
from rapikan.rules.word.W005_toc_stale import W005TOCStale
from rapikan.rules.word.W006_table_no_header import W006TableNoHeader
from rapikan.rules.word.W007_caption_missing import W007CaptionMissing
from rapikan.rules.word.W008_manual_spacing import W008ManualSpacing
from rapikan.rules.word.W010_double_space import W010DoubleSpace
from rapikan.rules.word.W012_chapter_order import W012ChapterOrder
from rapikan.rules.cross.X001_citation_vs_bib import X001CitationVsBib
from rapikan.rules.cross.X002_bib_uncited import X002BibUncited
from rapikan.rules.cross.X003_toc_vs_headings import X003TOCVsHeadings
from rapikan.rules.cross.X004_numbering_sequence import X004NumberingSequence
from rapikan.rules.word.B002_common_typos import B002CommonTypos


# --- Helpers ---
def make_para(
    text: str,
    para_id: str = "p_0001",
    style_name: str = "Normal",
    bold: bool = False,
    font_size_pt: float = 12.0,
    font_name: str = "Times New Roman",
    runs: list[Run] | None = None,
) -> Paragraph:
    effective = EffectiveStyle(
        bold=bold,
        font_size_pt=font_size_pt,
        font_name=font_name,
    )
    if runs is None:
        runs = [
            Run(
                text=text,
                effective_style=RunStyle(
                    bold=bold, font_size_pt=font_size_pt, font_name=font_name
                ),
            )
        ]
    return Paragraph(
        id=para_id,
        text=text,
        text_hash="dummyhash",
        style_name=style_name,
        effective_style=effective,
        runs=runs,
        is_blank_whitelist=(text.strip() == ""),
    )


# --- W001: Fake Heading ---
def test_w001_detects_bold_large_normal():
    rule = W001FakeHeading()
    # Paragraph with Normal style, bold=True, size=14pt >= threshold 13pt
    p = make_para("BAB I PENDAHULUAN", style_name="Normal", bold=True, font_size_pt=14.0)
    ir = IRDocument(paragraphs=[p])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 1
    assert findings[0].rule_id == "W001"
    assert findings[0].location.id == "p_0001"


def test_w001_ignores_proper_heading():
    rule = W001FakeHeading()
    p = make_para("BAB I PENDAHULUAN", style_name="Heading 1", bold=True, font_size_pt=14.0)
    ir = IRDocument(paragraphs=[p])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 0


# --- W002: Manual Numbering ---
def test_w002_detects_manual_numbering():
    rule = W002ManualNumbering()
    p1 = make_para("1. Pertama adalah poin penting.")
    p2 = make_para("a. Sub poin pertama.")
    ir = IRDocument(paragraphs=[p1, p2])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 2
    assert findings[0].rule_id == "W002"


def test_w002_ignores_list_style():
    rule = W002ManualNumbering()
    p = make_para("1. Poin dalam gaya list", style_name="List Number")
    ir = IRDocument(paragraphs=[p])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 0


# --- W003: Font Mix within paragraph ---
def test_w003_detects_mixed_font_in_paragraph():
    rule = W003FontMix()
    run1 = Run(text="Teks satu ", effective_style=RunStyle(font_name="Times New Roman", font_size_pt=12.0))
    run2 = Run(text="teks dua", effective_style=RunStyle(font_name="Arial", font_size_pt=12.0))
    p = make_para("Teks satu teks dua", runs=[run1, run2])
    ir = IRDocument(paragraphs=[p])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 1
    assert findings[0].rule_id == "W003"


def test_w003_uniform_font_passes():
    rule = W003FontMix()
    run1 = Run(text="Teks satu ", effective_style=RunStyle(font_name="Times New Roman", font_size_pt=12.0))
    run2 = Run(text="teks dua", effective_style=RunStyle(font_name="Times New Roman", font_size_pt=12.0))
    p = make_para("Teks satu teks dua", runs=[run1, run2])
    ir = IRDocument(paragraphs=[p])
    assert len(rule.check(ir, DEFAULT_PROFILE)) == 0


# --- W004: Inconsistent Margins across sections ---
def test_w004_detects_inconsistent_section_margins():
    rule = W004MarginSection()
    s0 = Section(index=0, margins=SectionMargins(top_twip=2268, bottom_twip=1701, left_twip=2268, right_twip=1701))
    s1 = Section(index=1, margins=SectionMargins(top_twip=1440, bottom_twip=1440, left_twip=1440, right_twip=1440))
    ir = IRDocument(sections=[s0, s1])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 1
    assert findings[0].rule_id == "W004"


# --- W005: TOC missing or not auto ---
def test_w005_detects_missing_or_manual_toc():
    rule = W005TOCStale()
    # Case 1: No auto TOC at all
    ir_no_toc = IRDocument(toc=TOCBlock(is_auto=False, entries=[]))
    findings = rule.check(ir_no_toc, DEFAULT_PROFILE)
    assert len(findings) >= 1
    assert findings[0].rule_id == "W005"

    # Case 2: Auto TOC with entries
    ir_auto_toc = IRDocument(toc=TOCBlock(is_auto=True, entries=[TOCEntry(text="BAB I", level=1, page_number=1)]))
    assert len(rule.check(ir_auto_toc, DEFAULT_PROFILE)) == 0


# --- W006: Table missing header row ---
def test_w006_detects_table_without_formatted_header():
    rule = W006TableNoHeader()
    # Table with row 0 not bold
    cell = Cell(
        address=CellAddress(table_index=0, row_index=0, col_index=0),
        paragraphs=[make_para("Kolom 1", bold=False)],
        is_header=False,
    )
    table = Table(id="t_0001", rows=[Row(index=0, cells=[cell], is_header=False)])
    ir = IRDocument(tables=[table])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 1
    assert findings[0].rule_id == "W006"


# --- W007: Caption missing for tables ---
def test_w007_detects_table_without_caption():
    rule = W007CaptionMissing()
    table = Table(id="t_0001", caption=None)
    ir = IRDocument(tables=[table], captions=[])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 1
    assert findings[0].rule_id == "W007"


# --- W008: Manual spacing (consecutive blank lines) ---
def test_w008_detects_consecutive_blank_paragraphs():
    rule = W008ManualSpacing()
    p1 = make_para("Paragraf pertama.")
    blank1 = make_para("", para_id="p_0002")
    blank2 = make_para("   ", para_id="p_0003")
    p2 = make_para("Paragraf kedua.", para_id="p_0004")
    ir = IRDocument(paragraphs=[p1, blank1, blank2, p2])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) >= 1
    assert findings[0].rule_id == "W008"


# --- W010: Double spaces ---
def test_w010_detects_double_spaces():
    rule = W010DoubleSpace()
    p = make_para("Ini adalah  kalimat dengan spasi ganda.")
    ir = IRDocument(paragraphs=[p])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 1
    assert findings[0].rule_id == "W010"


# --- W012: Chapter order violation ---
def test_w012_detects_wrong_chapter_order():
    rule = W012ChapterOrder()
    # BAB II appears before BAB I
    p1 = make_para("BAB II TINJAUAN PUSTAKA", para_id="p_0001", style_name="Heading 1")
    p2 = make_para("BAB I PENDAHULUAN", para_id="p_0002", style_name="Heading 1")
    ir = IRDocument(paragraphs=[p1, p2], headings=[p1, p2])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) >= 1
    assert findings[0].rule_id == "W012"


# --- X001: Citation without bibliography entry ---
def test_x001_detects_citation_missing_in_bib():
    rule = X001CitationVsBib()
    cite = InlineCitation(paragraph_id="p_0005", raw_text="(Sugiyono, 2019)", key="sugiyono, 2019")
    ir = IRDocument(inline_citations=[cite], bib_entries=[])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 1
    assert findings[0].rule_id == "X001"


# --- X002: Bibliography entry uncited ---
def test_x002_detects_uncited_bib_entry():
    rule = X002BibUncited()
    bib = BibEntry(paragraph_id="p_0050", raw_text="Sugiyono. (2019). Metode Penelitian.", key="sugiyono, 2019")
    ir = IRDocument(inline_citations=[], bib_entries=[bib])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 1
    assert findings[0].rule_id == "X002"


# --- X003: TOC entry != actual heading ---
def test_x003_detects_stale_toc_heading():
    rule = X003TOCVsHeadings()
    toc_entry = TOCEntry(text="BAB I PENDAHULUAN LAMA", level=1, page_number=1)
    heading_para = make_para("BAB I PENDAHULUAN BARU", style_name="Heading 1")
    ir = IRDocument(
        paragraphs=[heading_para],
        headings=[heading_para],
        toc=TOCBlock(is_auto=True, entries=[toc_entry]),
    )
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 1
    assert findings[0].rule_id == "X003"


# --- X004: Sequence numbering gap ---
def test_x004_detects_caption_sequence_gap():
    rule = X004NumberingSequence()
    c1 = Caption(id="p_0010", label="Tabel", number=1, chapter=None, full_text="Tabel 1 Data Sampel")
    c2 = Caption(id="p_0020", label="Tabel", number=3, chapter=None, full_text="Tabel 3 Hasil Uji")  # Skip 2!
    ir = IRDocument(captions=[c1, c2])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) == 1
    assert findings[0].rule_id == "X004"


# --- B002: Common Indonesian typos / non-standard words ---
def test_b002_detects_nonstandard_words():
    rule = B002CommonTypos()
    p = make_para("Praktek analisa data dilakukan secara sistematis.")
    ir = IRDocument(paragraphs=[p])
    findings = rule.check(ir, DEFAULT_PROFILE)
    assert len(findings) >= 2  # "praktek" and "analisa"
    assert any("praktik" in f.suggestion.lower() for f in findings)
    assert any("analisis" in f.suggestion.lower() for f in findings)


def test_w010_preserves_alignment_spaces_before_colon():
    """Requirement 4: Alignment spaces before colons (e.g. Nama      : Budi) must never be flagged."""
    rule = W010DoubleSpace()
    p1 = make_para("Nama      : Budi Santoso")
    p2 = make_para("NIM       : 12345678")
    p3 = make_para("Ini adalah  spasi ganda dalam teks prosa.")  # This should be flagged
    ir = IRDocument(paragraphs=[p1, p2, p3])
    findings = rule.check(ir, DEFAULT_PROFILE)

    # Only p3 is flagged, p1 and p2 are untouched
    assert len(findings) == 1
    assert findings[0].location.id == p3.id


def test_b002_ignores_bibliography_detected_by_heading_text():
    """Requirement 5: Bibliography heading text (even Normal style) protects entries from B002."""
    rule = B002CommonTypos()
    p_body = make_para("analisa data di bab 1.", para_id="p_0001")  # Should be flagged
    p_heading = make_para("DAFTAR PUSTAKA", para_id="p_0002")  # Heading text in Normal style
    p_bib1 = make_para("Sugiyono. (2020). Analisa Data Kualitatif. Alfabeta.", para_id="p_0003")  # Must NOT be flagged
    p_bib2 = make_para("Pratama, B. (2021). Praktek Pembelajaran Efektif.", para_id="p_0004")  # Must NOT be flagged

    ir = IRDocument(paragraphs=[p_body, p_heading, p_bib1, p_bib2])
    findings = rule.check(ir, DEFAULT_PROFILE)

    # Only body paragraph is flagged, bibliography entries are completely protected
    assert len(findings) == 1
    assert findings[0].location.id == "p_0001"


def test_w008_whitelist_approach_preserves_tracked_revisions_and_comments():
    """Requirement 2: Paragraphs containing revisions or comments are never flagged as blank."""
    rule = W008ManualSpacing()
    p_blank = make_para("", para_id="p_0001")
    p_blank.is_blank_whitelist = True

    p_rev = make_para("", para_id="p_0002")
    p_rev.has_revisions = True  # e.g. contains w:ins or w:del

    p_comm = make_para("", para_id="p_0003")
    p_comm.has_comments = True  # e.g. contains w:commentReference

    ir = IRDocument(paragraphs=[p_blank, p_rev, p_comm])
    findings = rule.check(ir, DEFAULT_PROFILE)

    # p_rev and p_comm are NOT considered blank, so no consecutive blank cluster is formed
    assert len(findings) == 0

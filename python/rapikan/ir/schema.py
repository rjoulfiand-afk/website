"""IR (Internal Representation) Pydantic models.

These models are the only interface between the converter and the rules.
Rules must never read the docx directly.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class LineSpacingRule(str, Enum):
    AUTO = "auto"
    EXACT = "exact"
    AT_LEAST = "atLeast"


class Provenance(str, Enum):
    DIRECT = "direct"
    STYLE = "style"
    DOC_DEFAULT = "doc_default"
    THEME = "theme"


class FieldType(str, Enum):
    PAGE = "PAGE"
    NUM_PAGES = "NUMPAGES"
    TOC = "TOC"
    SEQ = "SEQ"
    REF = "REF"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class LineSpacing(BaseModel):
    rule: LineSpacingRule
    value_pt: float  # always in points


class ThemeFont(BaseModel):
    major_font: str | None = None
    minor_font: str | None = None


class Theme(BaseModel):
    major_font: str | None = None
    minor_font: str | None = None


class Field_(BaseModel):
    """A Word field (PAGE, TOC, SEQ, …) embedded in a paragraph."""

    field_type: FieldType
    instruction: str  # raw field instruction string
    result: str | None = None  # cached result text if present


class EffectiveStyle(BaseModel):
    """Resolved formatting after walking the style inheritance chain."""

    font_name: str | None = None
    font_name_theme: str | None = None  # e.g. "majorHAnsi" before resolution
    font_size_pt: float | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    color: str | None = None  # hex RGB
    line_spacing: LineSpacing | None = None
    space_before_pt: float | None = None
    space_after_pt: float | None = None
    alignment: str | None = None  # "left", "center", "right", "justify"
    indent_left_cm: float | None = None
    indent_right_cm: float | None = None
    indent_first_line_cm: float | None = None


class ProvenanceMap(BaseModel):
    """Per-property source of each resolved value."""

    font_name: Provenance | None = None
    font_size_pt: Provenance | None = None
    bold: Provenance | None = None
    italic: Provenance | None = None
    underline: Provenance | None = None
    color: Provenance | None = None
    line_spacing: Provenance | None = None
    space_before_pt: Provenance | None = None
    space_after_pt: Provenance | None = None
    alignment: Provenance | None = None


class RunStyle(BaseModel):
    """Per-run formatting overrides."""

    font_name: str | None = None
    font_name_theme: str | None = None
    font_size_pt: float | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    color: str | None = None


class Run(BaseModel):
    text: str
    style: RunStyle = Field(default_factory=RunStyle)
    # Effective resolved style for this run (paragraph style + run override)
    effective_style: RunStyle = Field(default_factory=RunStyle)
    provenance: dict[str, Provenance] = Field(default_factory=dict)


class Paragraph(BaseModel):
    id: str  # e.g. "p_0001"
    text: str
    text_hash: str  # SHA-256 hex of text.encode("utf-8")
    style_name: str  # raw style name from docx
    effective_style: EffectiveStyle = Field(default_factory=EffectiveStyle)
    provenance: ProvenanceMap = Field(default_factory=ProvenanceMap)
    runs: list[Run] = Field(default_factory=list)
    fields: list[Field_] = Field(default_factory=list)
    # Structural safety flags (for W008, revisions, and document integrity)
    has_drawing: bool = False
    has_math: bool = False
    has_sect_pr: bool = False
    has_page_break: bool = False
    has_fields: bool = False
    has_bookmark: bool = False
    has_revisions: bool = False
    has_comments: bool = False
    has_sdt: bool = False
    has_alternate_content: bool = False
    is_blank_whitelist: bool = False
    is_table_separator: bool = False
    is_in_table_cell: bool = False
    # Position hints
    section_index: int = 0
    xml_ref: str | None = None  # XPath or similar for debugging


class CellAddress(BaseModel):
    table_index: int
    row_index: int
    col_index: int


class Cell(BaseModel):
    address: CellAddress
    paragraphs: list[Paragraph] = Field(default_factory=list)
    is_header: bool = False  # True if row 0 or marked as header


class Row(BaseModel):
    index: int
    cells: list[Cell] = Field(default_factory=list)
    is_header: bool = False


class Table(BaseModel):
    id: str  # e.g. "t_0001"
    rows: list[Row] = Field(default_factory=list)
    caption: str | None = None
    section_index: int = 0


class Caption(BaseModel):
    """Represents a caption paragraph for a figure or table."""

    id: str  # paragraph id of the caption
    label: str  # "Gambar" or "Tabel"
    number: int | None = None  # parsed sequence number
    chapter: int | None = None  # chapter prefix if present (e.g. "Gambar 3.2")
    full_text: str


class TOCEntry(BaseModel):
    text: str
    level: int
    page_number: int | None = None
    # Matched heading id (filled by X003 rule)
    matched_heading_id: str | None = None


class TOCBlock(BaseModel):
    is_auto: bool = False  # True if generated by a TOC field
    entries: list[TOCEntry] = Field(default_factory=list)
    is_stale: bool | None = None  # None = unknown


class SectionMargins(BaseModel):
    top_twip: int | None = None
    bottom_twip: int | None = None
    left_twip: int | None = None
    right_twip: int | None = None
    # Convenience cm values
    top_cm: float | None = None
    bottom_cm: float | None = None
    left_cm: float | None = None
    right_cm: float | None = None


class PageNumberInfo(BaseModel):
    fmt: str | None = None  # e.g. "decimal", "lowerRoman"
    start: int | None = None


class HeaderFooter(BaseModel):
    text: str | None = None
    has_page_field: bool = False


class Section(BaseModel):
    index: int
    margins: SectionMargins = Field(default_factory=SectionMargins)
    orientation: str = "portrait"  # "portrait" | "landscape"
    page_number: PageNumberInfo = Field(default_factory=PageNumberInfo)
    header_default: HeaderFooter | None = None
    header_first: HeaderFooter | None = None
    header_even: HeaderFooter | None = None
    footer_default: HeaderFooter | None = None
    footer_first: HeaderFooter | None = None
    footer_even: HeaderFooter | None = None
    different_first_page: bool = False


class InlineCitation(BaseModel):
    """A citation reference found in paragraph text."""

    paragraph_id: str
    raw_text: str  # e.g. "(Sugiyono, 2019)"
    key: str  # normalised key for matching


class BibEntry(BaseModel):
    """A bibliography / reference list entry."""

    paragraph_id: str
    raw_text: str
    key: str  # normalised key for matching


class DocDefaults(BaseModel):
    font_name: str | None = None
    font_size_pt: float | None = None
    line_spacing: LineSpacing | None = None


class IRDocument(BaseModel):
    """Top-level IR document."""

    # Ordered list of body elements (paragraphs + tables interleaved)
    paragraphs: list[Paragraph] = Field(default_factory=list)
    tables: list[Table] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    toc: TOCBlock = Field(default_factory=TOCBlock)
    captions: list[Caption] = Field(default_factory=list)
    inline_citations: list[InlineCitation] = Field(default_factory=list)
    bib_entries: list[BibEntry] = Field(default_factory=list)
    doc_defaults: DocDefaults = Field(default_factory=DocDefaults)
    theme: Theme = Field(default_factory=Theme)
    # Pre-flight document-level inspection flags
    has_revisions: bool = False
    has_comments: bool = False
    revision_count: int = 0
    comment_count: int = 0
    # Headings only (subset of paragraphs)
    headings: list[Paragraph] = Field(default_factory=list)

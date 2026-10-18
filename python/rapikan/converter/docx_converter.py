"""DOCX → IR converter.

Converts a .docx file into the IRDocument internal representation.
All XML parsing is done here; rules never touch the docx directly.
"""

from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET
from docx import Document
from docx.oxml.ns import qn
from lxml import etree

from rapikan.ir.schema import (
    BibEntry,
    Caption,
    Cell,
    CellAddress,
    DocDefaults,
    EffectiveStyle,
    Field_,
    FieldType,
    HeaderFooter,
    InlineCitation,
    IRDocument,
    LineSpacing,
    LineSpacingRule,
    PageNumberInfo,
    Paragraph,
    ProvenanceMap,
    Provenance,
    Row,
    Run,
    RunStyle,
    Section,
    SectionMargins,
    Table,
    TOCBlock,
    TOCEntry,
    Theme,
)
from rapikan.utils.twips import halfpt_to_pt, twips_to_cm, twips_to_pt

# ---------------------------------------------------------------------------
# Namespace map for lxml XPath
# ---------------------------------------------------------------------------
NSMAP = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"


def _w(tag: str) -> str:
    return f"{{{W}}}{tag}"


def _m(tag: str) -> str:
    return f"{{{M}}}{tag}"


def _mc(tag: str) -> str:
    return f"{{{MC}}}{tag}"


# ---------------------------------------------------------------------------
# Citation / bibliography regexes
# ---------------------------------------------------------------------------
_CITATION_RE = re.compile(
    r"\(([A-Z][^()]{1,80},\s*\d{4}(?:;\s*[A-Z][^()]{1,80},\s*\d{4})*)\)"
)
_BIB_STYLES = {"bibliography", "references", "daftar pustaka", "referensi"}


# ---------------------------------------------------------------------------
# Caption parsing
# ---------------------------------------------------------------------------
_CAPTION_RE = re.compile(
    r"^(Gambar|Tabel|Figure|Table|Grafik|Diagram)\s+(\d+)(?:\.(\d+))?"
    r"(?:\s|$|\.|\:)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _int_attr(elem: Any, attr: str, ns: str = W) -> int | None:
    """Get integer w: attribute from element."""
    val = elem.get(f"{{{ns}}}{attr}") if elem is not None else None
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _bool_attr(elem: Any, ns: str = W) -> bool | None:
    """Get boolean attribute from <w:b>, <w:i> etc. (presence = True, val='0' = False)."""
    if elem is None:
        return None
    val = elem.get(f"{{{ns}}}val")
    if val in (None, "1", "true", "on"):
        return True
    if val in ("0", "false", "off"):
        return False
    return True


def _text_of(elem: Any) -> str:
    """Extract all text from an lxml element including tail."""
    return "".join(elem.itertext())


# ---------------------------------------------------------------------------
# Theme extraction
# ---------------------------------------------------------------------------


def _extract_theme(docx_path: Path) -> Theme:
    """Read word/theme/theme1.xml from the ZIP to extract major/minor fonts."""
    theme = Theme()
    try:
        with zipfile.ZipFile(docx_path, "r") as zf:
            theme_names = [n for n in zf.namelist() if "theme/theme" in n and n.endswith(".xml")]
            if not theme_names:
                return theme
            raw = zf.read(theme_names[0])
            root = ET.fromstring(raw)

            A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

            def _a(tag: str) -> str:
                return f"{{{A_NS}}}{tag}"

            font_scheme = root.find(f".//{_a('fontScheme')}")
            if font_scheme is None:
                return theme

            major = font_scheme.find(f"{_a('majorFont')}/{_a('latin')}")
            minor = font_scheme.find(f"{_a('minorFont')}/{_a('latin')}")

            if major is not None:
                theme.major_font = major.get("typeface")
            if minor is not None:
                theme.minor_font = minor.get("typeface")
    except Exception:
        pass
    return theme


# ---------------------------------------------------------------------------
# Style resolution
# ---------------------------------------------------------------------------


class StyleResolver:
    """Resolves paragraph/run style by walking the basedOn chain."""

    def __init__(self, doc: Document, theme: Theme):
        self.theme = theme
        self._styles: dict[str, Any] = {}  # style_id -> lxml element

        styles_part = doc.part.styles
        if styles_part is not None:
            for s in styles_part.element.findall(_w("style")):
                sid = s.get(_w("styleId"))
                if sid:
                    self._styles[sid] = s

        self._doc_defaults = self._parse_doc_defaults(doc)

    def _parse_doc_defaults(self, doc: Document) -> DocDefaults:
        dd = DocDefaults()
        styles_part = doc.part.styles
        if styles_part is None:
            return dd
        doc_defaults_elem = styles_part.element.find(_w("docDefaults"))
        if doc_defaults_elem is None:
            return dd

        rpr = doc_defaults_elem.find(f".//{_w('rPr')}")
        if rpr is not None:
            sz = rpr.find(_w("sz"))
            if sz is not None:
                hp = _int_attr(sz, "val")
                if hp is not None:
                    dd.font_size_pt = halfpt_to_pt(hp)
            fonts = rpr.find(_w("rFonts"))
            if fonts is not None:
                dd.font_name = (
                    fonts.get(_w("ascii"))
                    or fonts.get(_w("hAnsi"))
                    or fonts.get(_w("eastAsia"))
                )

        ppr = doc_defaults_elem.find(f".//{_w('pPr')}")
        if ppr is not None:
            spacing = ppr.find(_w("spacing"))
            if spacing is not None:
                dd.line_spacing = _parse_spacing(spacing)

        return dd

    def _resolve_rpr(self, style_elem: Any) -> dict:
        """Get rPr dict for a style element, walking basedOn chain."""
        props: dict = {}
        chain = self._build_chain(style_elem)
        for s in reversed(chain):  # base first, then override
            rpr = s.find(f".//{_w('rPr')}")
            if rpr is not None:
                props.update(self._parse_rpr(rpr))
        return props

    def _resolve_ppr(self, style_elem: Any) -> dict:
        props: dict = {}
        chain = self._build_chain(style_elem)
        for s in reversed(chain):
            ppr = s.find(_w("pPr"))
            if ppr is None:
                # try inside the style body
                ppr = s.find(f".//{_w('pPr')}")
            if ppr is not None:
                props.update(self._parse_ppr(ppr))
        return props

    def _build_chain(self, style_elem: Any) -> list:
        chain = []
        visited = set()
        current = style_elem
        while current is not None:
            sid = current.get(_w("styleId"))
            if sid in visited:
                break
            visited.add(sid)
            chain.append(current)
            based_on = current.find(_w("basedOn"))
            if based_on is None:
                break
            parent_id = based_on.get(_w("val"))
            current = self._styles.get(parent_id)
        return chain

    def _parse_rpr(self, rpr: Any) -> dict:
        result = {}
        fonts = rpr.find(_w("rFonts"))
        if fonts is not None:
            ascii_theme = fonts.get(_w("asciiTheme")) or fonts.get(_w("hAnsiTheme"))
            ascii_val = fonts.get(_w("ascii")) or fonts.get(_w("hAnsi"))
            if ascii_theme:
                result["font_name_theme"] = ascii_theme
                # resolve theme
                if "major" in ascii_theme.lower():
                    result["font_name"] = self.theme.major_font
                elif "minor" in ascii_theme.lower():
                    result["font_name"] = self.theme.minor_font
            elif ascii_val:
                result["font_name"] = ascii_val

        sz = rpr.find(_w("sz"))
        if sz is not None:
            hp = _int_attr(sz, "val")
            if hp is not None:
                result["font_size_pt"] = halfpt_to_pt(hp)

        bold = rpr.find(_w("b"))
        if bold is not None:
            result["bold"] = _bool_attr(bold)

        italic = rpr.find(_w("i"))
        if italic is not None:
            result["italic"] = _bool_attr(italic)

        underline = rpr.find(_w("u"))
        if underline is not None:
            result["underline"] = True

        color_elem = rpr.find(_w("color"))
        if color_elem is not None:
            result["color"] = color_elem.get(_w("val"))

        return result

    def _parse_ppr(self, ppr: Any) -> dict:
        result = {}
        spacing = ppr.find(_w("spacing"))
        if spacing is not None:
            ls = _parse_spacing(spacing)
            if ls:
                result["line_spacing"] = ls
            before = _int_attr(spacing, "before")
            if before is not None:
                result["space_before_pt"] = twips_to_pt(before)
            after = _int_attr(spacing, "after")
            if after is not None:
                result["space_after_pt"] = twips_to_pt(after)

        jc = ppr.find(_w("jc"))
        if jc is not None:
            result["alignment"] = jc.get(_w("val"))

        ind = ppr.find(_w("ind"))
        if ind is not None:
            left = _int_attr(ind, "left")
            right = _int_attr(ind, "right")
            fl = _int_attr(ind, "firstLine")
            if left is not None:
                result["indent_left_cm"] = twips_to_cm(left)
            if right is not None:
                result["indent_right_cm"] = twips_to_cm(right)
            if fl is not None:
                result["indent_first_line_cm"] = twips_to_cm(fl)

        return result

    def resolve_paragraph(
        self, para_elem: Any, style_id: str | None
    ) -> tuple[EffectiveStyle, ProvenanceMap]:
        """Return (EffectiveStyle, ProvenanceMap) for a paragraph element."""
        provenance = ProvenanceMap()
        effective = EffectiveStyle()

        # 1. Doc defaults
        dd_props = {}
        if self._doc_defaults.font_name:
            dd_props["font_name"] = self._doc_defaults.font_name
        if self._doc_defaults.font_size_pt:
            dd_props["font_size_pt"] = self._doc_defaults.font_size_pt
        if self._doc_defaults.line_spacing:
            dd_props["line_spacing"] = self._doc_defaults.line_spacing

        # 2. Named style (+ basedOn chain)
        style_props: dict = {}
        if style_id and style_id in self._styles:
            style_elem = self._styles[style_id]
            rpr_props = self._resolve_rpr(style_elem)
            ppr_props = self._resolve_ppr(style_elem)
            style_props = {**rpr_props, **ppr_props}

        # 3. Direct paragraph formatting
        direct_props: dict = {}
        ppr = para_elem.find(_w("pPr"))
        if ppr is not None:
            rpr_direct = ppr.find(_w("rPr"))
            if rpr_direct is not None:
                direct_props.update(self._parse_rpr(rpr_direct))
            direct_props.update(self._parse_ppr(ppr))

        # Merge with provenance tracking
        all_keys = set(dd_props) | set(style_props) | set(direct_props)
        merged: dict = {}
        for k in all_keys:
            if k in direct_props:
                merged[k] = direct_props[k]
                prov = Provenance.DIRECT
            elif k in style_props:
                merged[k] = style_props[k]
                prov = Provenance.STYLE
            else:
                merged[k] = dd_props[k]
                prov = Provenance.DOC_DEFAULT

            # Set provenance on known fields
            if hasattr(provenance, k):
                try:
                    setattr(provenance, k, prov)
                except Exception:
                    pass

        # Apply to effective style
        for k, v in merged.items():
            if hasattr(effective, k):
                try:
                    setattr(effective, k, v)
                except Exception:
                    pass

        return effective, provenance

    def resolve_run(
        self,
        run_elem: Any,
        para_effective: EffectiveStyle,
        para_style_id: str | None,
    ) -> tuple[RunStyle, dict[str, Provenance]]:
        """Resolve run-level formatting."""
        # Style from paragraph's character style if any
        style_props: dict = {}
        run_ppr = run_elem.find(_w("rPr"))

        # Direct run properties
        direct_props: dict = {}
        if run_ppr is not None:
            direct_props = self._parse_rpr(run_ppr)

            # Check for rStyle
            r_style = run_ppr.find(_w("rStyle"))
            if r_style is not None:
                r_sid = r_style.get(_w("val"))
                if r_sid and r_sid in self._styles:
                    style_props = self._resolve_rpr(self._styles[r_sid])

        prov: dict[str, Provenance] = {}
        effective = RunStyle()

        para_props = {
            "font_name": para_effective.font_name,
            "font_size_pt": para_effective.font_size_pt,
            "bold": para_effective.bold,
            "italic": para_effective.italic,
        }

        all_keys = set(para_props) | set(style_props) | set(direct_props)
        merged: dict = {}
        for k in all_keys:
            if k in direct_props:
                merged[k] = direct_props[k]
                prov[k] = Provenance.DIRECT
            elif k in style_props:
                merged[k] = style_props[k]
                prov[k] = Provenance.STYLE
            elif para_props.get(k) is not None:
                merged[k] = para_props[k]
                prov[k] = Provenance.STYLE  # inherited from para

        for k, v in merged.items():
            if hasattr(effective, k):
                try:
                    setattr(effective, k, v)
                except Exception:
                    pass

        return effective, prov


# ---------------------------------------------------------------------------
# Spacing helper
# ---------------------------------------------------------------------------


def _parse_spacing(spacing_elem: Any) -> LineSpacing | None:
    line_val = _int_attr(spacing_elem, "line")
    line_rule = spacing_elem.get(_w("lineRule"))
    if line_val is None:
        return None

    if line_rule in (None, "auto"):
        # auto: value is in twentieths-of-a-point
        # 240 twips = 12pt × 1 line (single spacing at 12pt)
        value_pt = twips_to_pt(line_val)
        return LineSpacing(rule=LineSpacingRule.AUTO, value_pt=value_pt)
    elif line_rule == "exact":
        value_pt = twips_to_pt(line_val)
        return LineSpacing(rule=LineSpacingRule.EXACT, value_pt=value_pt)
    elif line_rule == "atLeast":
        value_pt = twips_to_pt(line_val)
        return LineSpacing(rule=LineSpacingRule.AT_LEAST, value_pt=value_pt)
    return None


# ---------------------------------------------------------------------------
# Field parsing
# ---------------------------------------------------------------------------


def _parse_fields(para_elem: Any) -> list[Field_]:
    """Extract Word fields (PAGE, TOC, SEQ) from a paragraph element."""
    fields: list[Field_] = []
    # Fields use fldChar begin/separate/end or fldSimple
    instruction_parts: list[str] = []
    in_instruction = False

    for child in para_elem.iter():
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "fldChar":
            fc_type = child.get(_w("fldCharType"))
            if fc_type == "begin":
                in_instruction = True
                instruction_parts = []
            elif fc_type == "end":
                in_instruction = False
                instruction = "".join(instruction_parts).strip()
                ft = _classify_field(instruction)
                fields.append(Field_(field_type=ft, instruction=instruction))
        elif tag == "instrText" and in_instruction:
            instruction_parts.append(child.text or "")
        elif tag == "fldSimple":
            instruction = child.get(_w("instr"), "").strip()
            ft = _classify_field(instruction)
            fields.append(Field_(field_type=ft, instruction=instruction))

    return fields


def _classify_field(instruction: str) -> FieldType:
    upper = instruction.strip().upper()
    if upper.startswith("PAGE"):
        return FieldType.PAGE
    if upper.startswith("NUMPAGES"):
        return FieldType.NUM_PAGES
    if upper.startswith("TOC"):
        return FieldType.TOC
    if upper.startswith("SEQ"):
        return FieldType.SEQ
    if upper.startswith("REF"):
        return FieldType.REF
    return FieldType.OTHER


# ---------------------------------------------------------------------------
# Section parsing
# ---------------------------------------------------------------------------


def _parse_section(sect_pr: Any, index: int) -> Section:
    section = Section(index=index)
    if sect_pr is None:
        return section

    # Margins
    pg_mar = sect_pr.find(_w("pgMar"))
    if pg_mar is not None:
        top = _int_attr(pg_mar, "top")
        bottom = _int_attr(pg_mar, "bottom")
        left = _int_attr(pg_mar, "left")
        right = _int_attr(pg_mar, "right")
        section.margins = SectionMargins(
            top_twip=top,
            bottom_twip=bottom,
            left_twip=left,
            right_twip=right,
            top_cm=twips_to_cm(top) if top is not None else None,
            bottom_cm=twips_to_cm(bottom) if bottom is not None else None,
            left_cm=twips_to_cm(left) if left is not None else None,
            right_cm=twips_to_cm(right) if right is not None else None,
        )

    # Orientation
    pg_sz = sect_pr.find(_w("pgSz"))
    if pg_sz is not None:
        orient = pg_sz.get(_w("orient"), "portrait")
        section.orientation = orient

    # Page number
    pg_num = sect_pr.find(_w("pgNumType"))
    if pg_num is not None:
        section.page_number = PageNumberInfo(
            fmt=pg_num.get(_w("fmt")),
            start=_int_attr(pg_num, "start"),
        )

    # Title page flag
    title_pg = sect_pr.find(_w("titlePg"))
    if title_pg is not None:
        section.different_first_page = True

    return section


# ---------------------------------------------------------------------------
# Header/footer extraction
# ---------------------------------------------------------------------------


def _extract_hf_text(doc: Document, rel_type: str) -> str | None:
    """Attempt to extract plain text from a header/footer part."""
    try:
        for rel in doc.part.rels.values():
            if rel_type in rel.reltype:
                part = rel.target_part
                texts = []
                for p in part.element.iter(_w("t")):
                    texts.append(p.text or "")
                return "".join(texts) or None
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# TOC detection
# ---------------------------------------------------------------------------


def _detect_toc(doc: Document) -> TOCBlock:
    """Detect auto TOC and extract entries."""
    toc_block = TOCBlock()
    entries: list[TOCEntry] = []

    for para in doc.paragraphs:
        style_name = para.style.name if para.style else ""
        # Check for TOC fields
        for field in _parse_fields(para._element):
            if field.field_type == FieldType.TOC:
                toc_block.is_auto = True

        # TOC entries are styled with "TOC N" styles
        if style_name.lower().startswith("toc") or style_name.lower().startswith("daftar"):
            level_match = re.search(r"\d+", style_name)
            level = int(level_match.group()) if level_match else 1
            text = para.text.strip()
            # Extract page number (last number in text)
            page_match = re.search(r"(\d+)\s*$", text)
            page_num = int(page_match.group(1)) if page_match else None
            entry_text = re.sub(r"\s+\d+\s*$", "", text).strip() if page_match else text
            entries.append(TOCEntry(text=entry_text, level=level, page_number=page_num))

    toc_block.entries = entries
    return toc_block


# ---------------------------------------------------------------------------
# Citation/bibliography extraction
# ---------------------------------------------------------------------------


def _extract_citations(paragraphs: list[Paragraph]) -> tuple[list[InlineCitation], list[BibEntry]]:
    citations: list[InlineCitation] = []
    bib_entries: list[BibEntry] = []
    in_bib_section = False

    for para in paragraphs:
        stripped = para.text.strip()
        # Detect bibliography heading even if Normal style
        if re.match(r"^(daftar pustaka|references|referensi|bibliografi)\b", stripped, re.IGNORECASE):
            in_bib_section = True
            continue
        elif in_bib_section and re.match(r"^(lampiran|appendix|bab\s+\w+)\b", stripped, re.IGNORECASE):
            in_bib_section = False

        # Inline citations (only outside bibliography section)
        if not in_bib_section:
            for match in _CITATION_RE.finditer(para.text):
                raw = match.group(0)
                key = _normalise_citation_key(match.group(1))
                citations.append(
                    InlineCitation(paragraph_id=para.id, raw_text=raw, key=key)
                )

        # Bibliography entries
        style_lower = para.style_name.lower()
        is_bib_style = any(s in style_lower for s in _BIB_STYLES)
        is_bib_heuristic = bool(re.match(r"^[A-Z][a-z]+,\s+[A-Z]\.", para.text))
        if in_bib_section or is_bib_style or is_bib_heuristic:
            if stripped:
                key = _normalise_bib_key(para.text)
                if key:
                    bib_entries.append(
                        BibEntry(paragraph_id=para.id, raw_text=para.text, key=key)
                    )

    return citations, bib_entries


def _normalise_citation_key(raw: str) -> str:
    """Normalise citation string for matching. e.g. 'Sugiyono, 2019'"""
    return raw.strip().lower()


def _normalise_bib_key(raw: str) -> str:
    """Extract normalised key from bibliography entry."""
    # Try to extract "Author, Year" pattern
    match = re.search(r"([A-Z][^\.,]+),.*?(\d{4})", raw)
    if match:
        return f"{match.group(1).strip()}, {match.group(2)}".lower()
    return raw[:50].lower()


# ---------------------------------------------------------------------------
# Caption extraction
# ---------------------------------------------------------------------------


def _extract_captions(paragraphs: list[Paragraph]) -> list[Caption]:
    captions: list[Caption] = []
    for para in paragraphs:
        # Check style name
        style_lower = para.style_name.lower()
        is_caption_style = "caption" in style_lower or "keterangan" in style_lower

        m = _CAPTION_RE.match(para.text.strip())
        if m:
            label = m.group(1).capitalize()
            chapter_or_num = m.group(2)
            sub_num = m.group(3)

            if sub_num:
                chapter = int(chapter_or_num)
                number = int(sub_num)
            else:
                chapter = None
                number = int(chapter_or_num)

            captions.append(
                Caption(
                    id=para.id,
                    label=label,
                    number=number,
                    chapter=chapter,
                    full_text=para.text.strip(),
                )
            )
        elif is_caption_style and para.text.strip():
            # Caption style but doesn't match pattern – store without number
            captions.append(
                Caption(
                    id=para.id,
                    label="Unknown",
                    number=None,
                    chapter=None,
                    full_text=para.text.strip(),
                )
            )

    return captions


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------


def convert_docx(path: Path) -> IRDocument:
    """Convert a .docx file to an IRDocument."""
    doc = Document(str(path))
    theme = _extract_theme(path)
    resolver = StyleResolver(doc, theme)

    ir = IRDocument(theme=theme)
    ir.doc_defaults = resolver._doc_defaults

    id_counter = [0]

    def next_para_id() -> str:
        id_counter[0] += 1
        return f"p_{id_counter[0]:04d}"

    table_counter = [0]

    def next_table_id() -> str:
        table_counter[0] += 1
        return f"t_{table_counter[0]:04d}"

    # Track sections – we process body elements
    section_index = 0
    sections: list[Section] = []

    # Process document body elements (paragraphs and tables in order)
    body = doc.element.body
    body_children = list(body)

    para_list: list[Paragraph] = []
    table_list: list[Table] = []

    for idx, child in enumerate(body_children):
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

        if tag == "p":
            is_tbl_sep = False
            if idx > 0 and idx < len(body_children) - 1:
                prev_tag = body_children[idx - 1].tag.split("}")[-1]
                next_tag = body_children[idx + 1].tag.split("}")[-1]
                if prev_tag == "tbl" and next_tag == "tbl":
                    is_tbl_sep = True

            para = _convert_paragraph(
                child,
                next_para_id(),
                resolver,
                section_index,
                is_table_separator=is_tbl_sep,
                is_in_table_cell=False,
            )
            para_list.append(para)

            # Check if this paragraph's pPr contains a sectPr
            ppr = child.find(_w("pPr"))
            if ppr is not None:
                sect_pr = ppr.find(_w("sectPr"))
                if sect_pr is not None:
                    sections.append(_parse_section(sect_pr, section_index))
                    section_index += 1

        elif tag == "tbl":
            table = _convert_table(child, next_table_id(), next_para_id, resolver, section_index)
            table_list.append(table)

        elif tag == "sectPr":
            # Final section
            sections.append(_parse_section(child, section_index))
            section_index += 1

    # If no sections were found, try the body's last sectPr
    if not sections:
        final_sect = body.find(_w("sectPr"))
        if final_sect is not None:
            sections.append(_parse_section(final_sect, 0))

    ir.paragraphs = para_list
    ir.tables = table_list
    ir.sections = sections
    ir.toc = _detect_toc(doc)
    ir.headings = [
        p for p in para_list
        if p.style_name.lower().startswith("heading") or
           re.match(r"^(bab|chapter)\s+\w", p.text.strip(), re.IGNORECASE)
    ]

    citations, bib_entries = _extract_citations(para_list)
    ir.inline_citations = citations
    ir.bib_entries = bib_entries
    ir.captions = _extract_captions(para_list)

    # Associate detected captions with tables
    table_captions = [c for c in ir.captions if c.label.lower() in ("tabel", "table")]
    for idx, table in enumerate(table_list):
        if idx < len(table_captions):
            table.caption = table_captions[idx].full_text

    # Document-level pre-flight inspection flags
    ir.has_revisions = any(p.has_revisions for p in para_list)
    ir.has_comments = any(p.has_comments for p in para_list)
    ir.revision_count = sum(1 for p in para_list if p.has_revisions)
    ir.comment_count = sum(1 for p in para_list if p.has_comments)

    return ir


def _convert_paragraph(
    elem: Any,
    para_id: str,
    resolver: StyleResolver,
    section_index: int,
    is_table_separator: bool = False,
    is_in_table_cell: bool = False,
) -> Paragraph:
    # Determine style
    ppr = elem.find(_w("pPr"))
    style_id = None
    style_name = "Normal"
    if ppr is not None:
        p_style = ppr.find(_w("pStyle"))
        if p_style is not None:
            style_id = p_style.get(_w("val"))
            style_name = style_id or "Normal"

    # Resolve style name from style element
    if style_id and style_id in resolver._styles:
        name_elem = resolver._styles[style_id].find(_w("name"))
        if name_elem is not None:
            style_name = name_elem.get(_w("val")) or style_id

    effective, provenance = resolver.resolve_paragraph(elem, style_id)

    # Extract text
    text_parts = []
    for t in elem.iter(_w("t")):
        text_parts.append(t.text or "")
    text = "".join(text_parts)

    # Extract runs
    runs = _convert_runs(elem, effective, style_id, resolver)

    # Extract fields
    fields = _parse_fields(elem)

    # Structural safety inspections (W008 non-negotiable guards)
    has_drawing = bool(elem.findall(f".//{_w('drawing')}") or elem.findall(f".//{_w('pict')}"))
    has_math = bool(elem.findall(f".//{{{M}}}oMath") or elem.findall(f".//{{{M}}}oMathPara"))
    has_sect_pr = bool(ppr is not None and ppr.find(_w("sectPr")) is not None)
    has_page_break = bool(
        elem.findall(f".//{_w('br')}[@{{{W}}}type='page']")
        or elem.findall(f".//{_w('lastRenderedPageBreak')}")
    )
    has_bookmark = bool(elem.findall(f".//{_w('bookmarkStart')}"))
    has_revisions = bool(
        elem.findall(f".//{_w('ins')}")
        or elem.findall(f".//{_w('del')}")
        or elem.findall(f".//{_w('moveFrom')}")
        or elem.findall(f".//{_w('moveTo')}")
        or elem.findall(f".//{_w('pPrChange')}")
        or elem.findall(f".//{_w('rPrChange')}")
    )
    has_comments = bool(
        elem.findall(f".//{_w('commentRangeStart')}")
        or elem.findall(f".//{_w('commentRangeEnd')}")
        or elem.findall(f".//{_w('commentReference')}")
    )
    has_sdt = bool(elem.findall(f".//{_w('sdt')}"))
    has_alternate_content = bool(
        elem.findall(f".//{{{MC}}}AlternateContent")
        or elem.findall(f".//{_w('object')}")
    )

    # Whitelist blank check (Requirement 2):
    # Paragraph can be removed ONLY if its contents are solely w:pPr (without sectPr/revisions)
    # and w:r containing solely whitespace text.
    is_blank_whitelist = False
    if not is_table_separator and not is_in_table_cell and not text.strip():
        if not (
            has_drawing
            or has_math
            or has_sect_pr
            or has_page_break
            or has_bookmark
            or has_revisions
            or has_comments
            or has_sdt
            or has_alternate_content
            or bool(fields)
        ):
            valid_children = True
            for child in elem:
                ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if ctag == "pPr":
                    if child.find(_w("sectPr")) is not None or child.find(_w("pPrChange")) is not None:
                        valid_children = False
                        break
                elif ctag == "r":
                    for r_child in child:
                        rtag = r_child.tag.split("}")[-1] if "}" in r_child.tag else r_child.tag
                        if rtag == "t":
                            if r_child.text and r_child.text.strip():
                                valid_children = False
                                break
                        elif rtag == "rPr":
                            if r_child.find(_w("rPrChange")) is not None:
                                valid_children = False
                                break
                        else:
                            valid_children = False
                            break
                    if not valid_children:
                        break
                else:
                    valid_children = False
                    break
            is_blank_whitelist = valid_children

    return Paragraph(
        id=para_id,
        text=text,
        text_hash=_sha256(text),
        style_name=style_name,
        effective_style=effective,
        provenance=provenance,
        runs=runs,
        fields=fields,
        has_drawing=has_drawing,
        has_math=has_math,
        has_sect_pr=has_sect_pr,
        has_page_break=has_page_break,
        has_fields=bool(fields),
        has_bookmark=has_bookmark,
        has_revisions=has_revisions,
        has_comments=has_comments,
        has_sdt=has_sdt,
        has_alternate_content=has_alternate_content,
        is_blank_whitelist=is_blank_whitelist,
        is_table_separator=is_table_separator,
        is_in_table_cell=is_in_table_cell,
        section_index=section_index,
    )


def _convert_runs(
    para_elem: Any,
    para_effective: EffectiveStyle,
    style_id: str | None,
    resolver: StyleResolver,
) -> list[Run]:
    runs: list[Run] = []
    for r_elem in para_elem.findall(_w("r")):
        # Text
        text_parts = []
        for t in r_elem.findall(_w("t")):
            text_parts.append(t.text or "")
        text = "".join(text_parts)

        rpr = r_elem.find(_w("rPr"))
        # Raw style
        raw_style = RunStyle()
        if rpr is not None:
            parsed = resolver._parse_rpr(rpr)
            for k, v in parsed.items():
                if hasattr(raw_style, k):
                    try:
                        setattr(raw_style, k, v)
                    except Exception:
                        pass

        effective_run, prov = resolver.resolve_run(r_elem, para_effective, style_id)

        runs.append(
            Run(
                text=text,
                style=raw_style,
                effective_style=effective_run,
                provenance=prov,
            )
        )
    return runs


def _convert_table(
    tbl_elem: Any,
    table_id: str,
    next_para_id: "callable",
    resolver: StyleResolver,
    section_index: int,
) -> Table:
    table = Table(id=table_id, section_index=section_index)
    rows = []
    for row_idx, tr in enumerate(tbl_elem.findall(_w("tr"))):
        cells = []
        is_header_row = row_idx == 0
        for col_idx, tc in enumerate(tr.findall(_w("tc"))):
            cell_paras = []
            for p in tc.findall(_w("p")):
                cell_paras.append(
                    _convert_paragraph(
                        p,
                        next_para_id(),
                        resolver,
                        section_index,
                        is_table_separator=False,
                        is_in_table_cell=True,
                    )
                )
            cells.append(
                Cell(
                    address=CellAddress(
                        table_index=int(table_id.split("_")[1]) - 1,
                        row_index=row_idx,
                        col_index=col_idx,
                    ),
                    paragraphs=cell_paras,
                    is_header=is_header_row,
                )
            )
        rows.append(Row(index=row_idx, cells=cells, is_header=is_header_row))
    table.rows = rows
    return table

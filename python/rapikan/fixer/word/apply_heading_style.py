"""W001 Fixer: Converts fake heading to official Word Heading style following profile.

Guards:
1. Style Heading mengikuti profil kampus (font, size, alignment).
2. Format langsung lama (bold, ukuran, font, warna, perataan, spasi) dibersihkan total.
3. Menghindari penomoran ganda jika teks sudah mengandung penomoran manual seperti 'BAB I' atau '1.1'.
"""

from __future__ import annotations

import re
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from rapikan.fixer.base import BaseFixer
from rapikan.ir.finding_schema import Finding
from rapikan.rules.campus_profile import DEFAULT_PROFILE, CampusProfile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _w(tag: str) -> str:
    return f"{{{W}}}{tag}"


def _get_heading_style_name(doc: Document, level: int = 1) -> str:
    """Find available Heading style in doc (handles Indonesian 'Judul 1' and English 'Heading 1')."""
    candidates = [
        f"Heading {level}",
        f"Heading{level}",
        f"Judul {level}",
        f"Judul{level}",
    ]
    style_names = {s.name for s in doc.styles}
    for c in candidates:
        if c in style_names:
            return c
    return f"Heading {level}"


class W001HeadingFixer(BaseFixer):
    rule_id = "W001"

    def __init__(self, profile: CampusProfile | None = None):
        self.profile = profile or DEFAULT_PROFILE

    def fix(self, doc: Document, finding: Finding) -> bool:
        para_id = finding.location.id
        m = re.search(r"p_(\d+)", para_id)
        if not m:
            return False

        para_idx = int(m.group(1)) - 1
        if para_idx < 0 or para_idx >= len(doc.paragraphs):
            return False

        para = doc.paragraphs[para_idx]
        text = para.text.strip()

        # Determine level: "2.1.1" -> Heading 3, "2.1" -> Heading 2, "BAB I" -> Heading 1
        if re.match(r"^\d+\.\d+\.\d+", text):
            level = 3
        elif re.match(r"^\d+\.\d+", text):
            level = 2
        else:
            level = 1

        target_style_name = _get_heading_style_name(doc, level)

        # Apply standard Word style
        try:
            para.style = doc.styles[target_style_name]
        except KeyError:
            para.style = target_style_name

        # Synchronize heading style definition with profile typography (Requirement 1)
        try:
            style = doc.styles[target_style_name]
            if hasattr(style, 'font'):
                if self.profile.heading_font.name:
                    style.font.name = self.profile.heading_font.name
                if self.profile.heading_font.size_pt:
                    style.font.size = Pt(self.profile.heading_font.size_pt)
                style.font.bold = True
                if hasattr(style.font, "color"):
                    style.font.color.rgb = RGBColor(0, 0, 0)
            if hasattr(style, 'paragraph_format'):
                if level == 1 and re.match(r"^(bab|chapter)\b", text, re.IGNORECASE):
                    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                if hasattr(self.profile, 'body_spacing'):
                    style.paragraph_format.space_before = Pt(self.profile.body_spacing.space_before_pt)
                    style.paragraph_format.space_after = Pt(self.profile.body_spacing.space_after_pt)
        except Exception:
            pass

        # Clean direct run-level overrides, PRESERVING meaningful formatting (italic, subscript, superscript)
        for run in para.runs:
            run.bold = None
            run.font.size = None
            run.font.name = None
            if hasattr(run.font, "color"):
                run.font.color.rgb = None
            # DO NOT clear run.italic, run.font.subscript, or run.font.superscript!

        # Clean direct paragraph-level overrides so the style cleanly controls formatting
        if level == 1 and re.match(r"^(bab|chapter)\b", text, re.IGNORECASE):
            para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        para.paragraph_format.space_before = Pt(self.profile.body_spacing.space_before_pt)
        para.paragraph_format.space_after = Pt(self.profile.body_spacing.space_after_pt)
        para.paragraph_format.line_spacing = None

        # Guard against double numbering:
        # If the paragraph already has manual "BAB I" or "1.1", ensure pPr does not have numPr
        ppr = para._element.find(_w("pPr"))
        if ppr is not None:
            num_pr = ppr.find(_w("numPr"))
            if num_pr is not None:
                # If manual chapter/number pattern is present in text, remove numPr to prevent "1. BAB I"
                if re.match(r"^(BAB\s+[IVXLCDM\d]+|\d+\.\d+)", text, re.IGNORECASE):
                    ppr.remove(num_pr)

        return True

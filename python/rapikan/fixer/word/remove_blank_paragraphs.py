"""W008 Fixer: Removes consecutive blank/empty paragraphs with non-negotiable structural guards.

Safety Guards:
1. Hanya sentuh paragraf di doc.element.body (BUKAN header, footer, atau sel tabel w:tc).
2. Paragraf tidak boleh dihapus jika mengandung:
   - w:drawing atau w:pict (gambar)
   - m:oMath atau m:oMathPara (rumus/persamaan matematika)
   - w:sectPr (section break)
   - w:br type="page" atau lastRenderedPageBreak (page break)
   - w:fldChar / w:fldSimple (fields)
   - w:bookmarkStart (bookmark)
   - Berada di antara dua tabel berurutan (<tbl> <p> <tbl>)
"""

from __future__ import annotations

from typing import Any
from docx import Document
from rapikan.fixer.base import BaseFixer
from rapikan.ir.finding_schema import Finding

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _w(tag: str) -> str:
    return f"{{{W}}}{tag}"


MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"


def _is_safe_to_remove(p_elem: Any, body_children: list[Any]) -> bool:
    """Strict Whitelist Approach (Requirement 2):
    Paragraph may ONLY be removed if its contents are strictly w:pPr (without sectPr/revisions)
    and w:r elements containing solely whitespace text.
    Must preserve mc:AlternateContent, w:object, w:sdt, w:ins/w:del, comments, math, drawings,
    bookmarks, fields, page breaks, and table separators.
    """
    # 1. Must be in body, not inside w:tc (table cell) or header/footer
    parent = p_elem.getparent()
    if parent is None or not parent.tag.endswith("body"):
        return False

    # 2. Must not sit between two tables (<tbl> <p> <tbl>)
    try:
        idx = body_children.index(p_elem)
        if idx > 0 and idx < len(body_children) - 1:
            prev_tag = body_children[idx - 1].tag.split("}")[-1]
            next_tag = body_children[idx + 1].tag.split("}")[-1]
            if prev_tag == "tbl" and next_tag == "tbl":
                return False
    except ValueError:
        pass

    # 3. Must have no visible non-whitespace text
    text = "".join(p_elem.itertext()).strip()
    if text:
        return False

    # 4. Strictly inspect all child elements according to whitelist
    for child in p_elem:
        ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if ctag == "pPr":
            # pPr cannot contain sectPr or pPrChange (tracked revision)
            if child.find(_w("sectPr")) is not None or child.find(_w("pPrChange")) is not None:
                return False
        elif ctag == "r":
            # Run children can ONLY be rPr (no revisions) and whitespace-only t
            for r_child in child:
                rtag = r_child.tag.split("}")[-1] if "}" in r_child.tag else r_child.tag
                if rtag == "t":
                    if r_child.text and r_child.text.strip():
                        return False
                elif rtag == "rPr":
                    if r_child.find(_w("rPrChange")) is not None:
                        return False
                else:
                    # drawing, pict, object, br, fldChar, footnote, etc.
                    return False
        else:
            # Any non-whitelisted element: mc:AlternateContent, w:object, w:sdt,
            # w:ins, w:del, w:commentRangeStart, w:commentRangeEnd, w:commentReference,
            # w:bookmarkStart, w:fldSimple, m:oMath, etc.
            return False

    return True


class W008BlankParagraphFixer(BaseFixer):
    rule_id = "W008"

    def fix(self, doc: Document, finding: Finding) -> bool:
        body = doc.element.body
        body_children = list(body)
        modified = False

        # Find paragraphs in body only
        body_paras = [child for child in body_children if child.tag.endswith("}p")]

        consecutive_blanks = []
        paras_to_remove = []

        for p_elem in body_paras:
            if _is_safe_to_remove(p_elem, body_children):
                consecutive_blanks.append(p_elem)
            else:
                if len(consecutive_blanks) >= 2:
                    paras_to_remove.extend(consecutive_blanks)
                consecutive_blanks = []

        # Check trailing blanks
        if len(consecutive_blanks) >= 2:
            paras_to_remove.extend(consecutive_blanks)

        for p_elem in paras_to_remove:
            parent = p_elem.getparent()
            if parent is not None:
                parent.remove(p_elem)
                modified = True

        return modified

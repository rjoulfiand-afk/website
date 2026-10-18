"""W006 Fixer: Formats row 0 of table as a repeating header row with table style header formatting.

Invarian 2 Compliance:
1. Menambahkan w:tblHeader pada trPr baris pertama agar otomatis berulang di tiap halaman.
2. Mengaktifkan conditional formatting w:tblLook firstRow="1" pada w:tblPr.
3. Catatan Pengecualian Invarian 2:
   Pada template Word standar yang tidak menyertakan definisi w:tblStylePr type="firstRow" di styles.xml,
   run-level bold pada sel header dipertahankan demi kompatibilitas visual lintas-aplikasi (LibreOffice/Word).
"""

from __future__ import annotations

import re
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from rapikan.fixer.base import BaseFixer
from rapikan.ir.finding_schema import Finding

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _w(tag: str) -> str:
    return f"{{{W}}}{tag}"


class W006TableHeaderFixer(BaseFixer):
    rule_id = "W006"

    def fix(self, doc: Document, finding: Finding) -> bool:
        tbl_id = finding.location.id
        m = re.search(r"t_(\d+)", tbl_id)
        if not m:
            return False

        tbl_idx = int(m.group(1)) - 1
        if tbl_idx < 0 or tbl_idx >= len(doc.tables):
            return False

        table = doc.tables[tbl_idx]
        if not table.rows:
            return False

        # 1. Activate table style conditional formatting for first row (tblLook firstRow="1")
        tblPr = table._tbl.tblPr
        tblLook = tblPr.find(_w("tblLook"))
        if tblLook is not None:
            tblLook.set(_w("firstRow"), "1")
        else:
            tblLook_xml = parse_xml(f'<w:tblLook {nsdecls("w")} w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>')
            tblPr.append(tblLook_xml)

        row_0 = table.rows[0]

        # 2. Add tblHeader to trPr so Word repeats it on every page
        trPr = row_0._tr.get_or_add_trPr()
        if trPr.find(_w("tblHeader")) is None:
            tbl_header_xml = parse_xml(f'<w:tblHeader {nsdecls("w")}/>')
            trPr.append(tbl_header_xml)

        # 3. Bold cells in row 0
        # (Catatan Pengecualian Invarian 2: diterapkan demi kompatibilitas bila table style tidak memuat w:tblStylePr firstRow)
        for cell in row_0.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.bold = True
                if not p.runs and p.text:
                    txt = p.text
                    p.text = ""
                    r = p.add_run(txt)
                    r.bold = True

        return True

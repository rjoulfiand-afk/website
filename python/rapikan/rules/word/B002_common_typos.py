"""B002 – Pola Kesalahan Kata Baku Bahasa Indonesia (Indonesian Typo & Non-Standard Words).

Non-negotiable guards:
1. changes_text = True (CANNOT run in batch 'Rapikan Semua Sekaligus'; strictly via rewrite proposals).
2. Tidak boleh menyentuh:
   - Kutipan langsung (teks di dalam tanda kutip "...", “...”, '...', «...» atau style Kutipan/Quote)
   - Daftar Pustaka / Referensi (style pustaka atau paragraf bib_entries)
   - Nama diri (kata berhuruf kapital di tengah kalimat)
   - URL/link (http://, https://, www.) atau blok kode
3. Bentuk turunan (merubah -> mengubah, dirubah -> diubah) ditangani lewat kamus eksplisit.
4. Preservasi huruf besar/kecil (UPPER, Title, lower).
"""

from __future__ import annotations

import re
from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile

# Explicit inflection dictionary: non-standard -> standard KBBI
EXPLICIT_TYPO_MAP: dict[str, str] = {
    # ubah vs rubah
    "merubah": "mengubah",
    "dirubah": "diubah",
    "merubahnya": "mengubahnya",
    "dirubahnya": "diubahnya",
    "terubah": "terubah",
    # praktik vs praktek
    "praktek": "praktik",
    "prakteknya": "praktiknya",
    "berpraktek": "berpraktik",
    "mempraktekkan": "mempraktikkan",
    "dipraktekkan": "dipraktikkan",
    # analisis vs analisa
    "analisa": "analisis",
    "menganalisa": "menganalisis",
    "dianalisa": "dianalisis",
    "penganalisaan": "penganalisisan",
    # teoretis vs teoritis
    "teoritis": "teoretis",
    "hipotesa": "hipotesis",
    "obyek": "objek",
    "subyek": "subjek",
    "obyektif": "objektif",
    "subyektif": "subjektif",
    "jadual": "jadwal",
    "resiko": "risiko",
    "beresiko": "berisiko",
    "hirarki": "hierarki",
    "mempersilahkan": "mempersilakan",
    "dipersilahkan": "dipersilakan",
    "kualitet": "kualitas",
    "kuantitet": "kuantitas",
    "sistim": "sistem",
    "azas": "asas",
    "berazas": "berasas",
    "antri": "antre",
    "mengantri": "mengantre",
    "antrian": "antrean",
    "aktifitas": "aktivitas",
    "efektifitas": "efektivitas",
    "kreatifitas": "kreativitas",
    "produktifitas": "produktivitas",
    "standarisasi": "standardisasi",
    "ekstrim": "ekstrem",
    "konkrit": "konkret",
}

_TYPO_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in EXPLICIT_TYPO_MAP) + r")\b",
    re.IGNORECASE,
)

# Regex to find quoted spans to ignore
_QUOTED_SPAN_RE = re.compile(
    r'("[^"]*?"|“[^”]*?”|\'[^\']*?\'|‘[^’]*?’|«[^»]*?»)'
)

_URL_RE = re.compile(r"(https?://\S+|www\.\S+|\S+@\S+)")


def _match_casing(original: str, replacement: str) -> str:
    """Preserve ALL CAPS, TitleCase, or lowercase."""
    if original.isupper():
        return replacement.upper()
    if original.istitle():
        return replacement.title()
    return replacement.lower()


class B002CommonTypos(BaseRule):
    rule_id = "B002"
    rule_name = "Pola Kata Tidak Baku / Ejaan (Usulan Tulis-Ulang)"
    phase = 1
    requires_render = False
    requires_llm = False
    changes_text = True  # NON-NEGOTIABLE: cannot run in batch
    applies_to = ["*"]

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []

        # Identify bibliography paragraph IDs to skip
        bib_para_ids = {b.paragraph_id for b in ir.bib_entries}
        in_bibliography = False

        for p in ir.paragraphs:
            stripped = p.text.strip()
            # Requirement 5: Detect bibliography heading text (including fake heading in Normal style)
            if re.match(r"^(daftar pustaka|references|referensi|bibliografi)\b", stripped, re.IGNORECASE):
                in_bibliography = True
                continue
            elif in_bibliography and re.match(r"^(lampiran|appendix|bab\s+\w+)\b", stripped, re.IGNORECASE):
                in_bibliography = False

            if in_bibliography:
                continue

            # 1. Skip bibliography / references
            if p.id in bib_para_ids:
                continue
            style_name_lower = p.style_name.lower()
            if any(s in style_name_lower for s in ("bibliography", "references", "pustaka", "referensi")):
                continue

            # 2. Skip block quote styles or code styles
            if any(s in style_name_lower for s in ("quote", "kutipan", "code", "source")):
                continue

            text = p.text
            if not text.strip():
                continue

            # Find ranges of quoted spans to exclude
            quote_spans: list[tuple[int, int]] = [
                m.span() for m in _QUOTED_SPAN_RE.finditer(text)
            ]

            # Find ranges of URLs/code to exclude
            url_spans: list[tuple[int, int]] = [
                m.span() for m in _URL_RE.finditer(text)
            ]

            excluded_spans = quote_spans + url_spans

            for match in _TYPO_REGEX.finditer(text):
                m_start, m_end = match.span()

                # Check if match is inside excluded spans
                if any(start <= m_start and m_end <= end for start, end in excluded_spans):
                    continue

                found_word = match.group(1)
                lower_word = found_word.lower()
                base_replacement = EXPLICIT_TYPO_MAP.get(lower_word)
                if not base_replacement:
                    continue

                # Guard 3: Skip proper names (Capitalized word in middle of sentence)
                # If word is capitalized, verify if it's the first word of sentence/paragraph
                if found_word.istitle():
                    prev_text = text[:m_start].strip()
                    if prev_text:
                        last_char = prev_text[-1]
                        # Not after a sentence-ending punctuation -> likely a proper noun/name
                        if last_char not in (".", "!", "?", ":", "\n"):
                            continue

                standard_word = _match_casing(found_word, base_replacement)

                start_ctx = max(0, m_start - 30)
                end_ctx = min(len(text), m_end + 30)
                snippet = text[start_ctx:end_ctx]

                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=Severity.WARNING,
                        confidence=0.95,
                        location=Location(
                            type=LocationType.PARAGRAPH,
                            id=p.id,
                            label=f"Paragraf {p.id}",
                            section_index=p.section_index,
                        ),
                        evidence=Evidence(
                            snippet=f"...{snippet}...",
                            detail=f"Kata tidak baku: '{found_word}' -> '{standard_word}'",
                            extra={
                                "from_word": found_word,
                                "to_word": standard_word,
                                "match_start": m_start,
                                "match_end": m_end,
                            },
                        ),
                        auto_fixable=False,  # MUST NOT run in batch; requires rewrite proposal approval
                        changes_text=True,    # Explicit flag
                        suggestion=(
                            f"Usulan perbaikan: ganti kata '{found_word}' dengan '{standard_word}' "
                            "sesuai rujukan KBBI daring."
                        ),
                        guide_module_slug="word-bahasa-indonesia",
                    )
                )

        return findings

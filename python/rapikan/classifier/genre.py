"""Multi-Genre Blueprint & Classifier for Academic and Professional Documents.

Supports Indonesian academic document genres:
1. Skripsi / Tugas Akhir / Tesis (Monograf lengkap Bab I - V)
2. Makalah / Paper Akademik (Karya tulis ringkas tanpa bab formal)
3. Laporan Magang / Praktik Kerja Lapangan (Bab I - IV, fokus instansi)
4. Proposal Penelitian / Proposal Skripsi (Bab I - III, fokus usulan & jadwal)
5. Custom / Generic
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from rapikan.ir.schema import IRDocument


class Genre(str, Enum):
    SKRIPSI = "skripsi"
    MAKALAH = "makalah"
    LAPORAN_MAGANG = "laporan_magang"
    PROPOSAL_PENELITIAN = "proposal_penelitian"
    CUSTOM = "custom"


class GenreBlueprint(BaseModel):
    """Structural blueprint and requirements for a specific document genre."""

    genre: Genre
    name: str
    description: str
    expected_chapters: list[str]
    keywords: list[str] = Field(default_factory=list)
    max_bab: int = 5
    requires_front_matter: bool = True
    has_roman_page_numbers: bool = True


GENRE_BLUEPRINTS: dict[Genre, GenreBlueprint] = {
    Genre.SKRIPSI: GenreBlueprint(
        genre=Genre.SKRIPSI,
        name="Skripsi / Tugas Akhir / Tesis",
        description="Karya ilmiah monograf lengkap dengan 5 bab (Pendahuluan hingga Penutup) dan bagian awal formal.",
        expected_chapters=[
            "HALAMAN JUDUL",
            "LEMBAR PERSETUJUAN",
            "LEMBAR PENGESAHAN",
            "ABSTRAK",
            "ABSTRACT",
            "KATA PENGANTAR",
            "DAFTAR ISI",
            "DAFTAR TABEL",
            "DAFTAR GAMBAR",
            "BAB I",
            "BAB II",
            "BAB III",
            "BAB IV",
            "BAB V",
            "DAFTAR PUSTAKA",
            "LAMPIRAN",
        ],
        keywords=[
            "skripsi",
            "tugas akhir",
            "tesis",
            "disertasi",
            "sidang sarjana",
            "program studi",
            "diajukan untuk memenuhi",
        ],
        max_bab=5,
        requires_front_matter=True,
        has_roman_page_numbers=True,
    ),
    Genre.MAKALAH: GenreBlueprint(
        genre=Genre.MAKALAH,
        name="Makalah / Paper Akademik",
        description="Karya tulis ilmiah atau tugas perkuliahan tanpa penomoran bab formal (BAB I-V).",
        expected_chapters=[
            "JUDUL",
            "ABSTRAK",
            "PENDAHULUAN",
            "PEMBAHASAN",
            "KESIMPULAN",
            "PENUTUP",
            "DAFTAR PUSTAKA",
        ],
        keywords=[
            "makalah",
            "paper",
            "artikel ilmiah",
            "kajian literatur",
            "latar belakang masalah",
        ],
        max_bab=0,
        requires_front_matter=False,
        has_roman_page_numbers=False,
    ),
    Genre.LAPORAN_MAGANG: GenreBlueprint(
        genre=Genre.LAPORAN_MAGANG,
        name="Laporan Magang / Praktik Kerja",
        description="Laporan kegiatan praktik kerja lapangan / magang di industri atau instansi.",
        expected_chapters=[
            "HALAMAN JUDUL",
            "LEMBAR PENGESAHAN",
            "KATA PENGANTAR",
            "DAFTAR ISI",
            "DAFTAR TABEL",
            "DAFTAR GAMBAR",
            "BAB I",
            "BAB II",
            "BAB III",
            "BAB IV",
            "DAFTAR PUSTAKA",
            "LAMPIRAN",
        ],
        keywords=[
            "laporan magang",
            "praktik kerja lapangan",
            "pkl",
            "kerja praktek",
            "kkn",
            "tempat magang",
            "pembimbing lapangan",
            "profil instansi",
            "profil perusahaan",
            "gambaran umum perusahaan",
        ],
        max_bab=4,
        requires_front_matter=True,
        has_roman_page_numbers=True,
    ),
    Genre.PROPOSAL_PENELITIAN: GenreBlueprint(
        genre=Genre.PROPOSAL_PENELITIAN,
        name="Proposal Penelitian / Skripsi",
        description="Rancangan usulan penelitian sebelum riset lapangan (Bab I - III disertai jadwal penelitian).",
        expected_chapters=[
            "HALAMAN JUDUL",
            "LEMBAR PERSETUJUAN",
            "DAFTAR ISI",
            "DAFTAR TABEL",
            "DAFTAR GAMBAR",
            "BAB I",
            "BAB II",
            "BAB III",
            "JADWAL PENELITIAN",
            "DAFTAR PUSTAKA",
            "LAMPIRAN",
        ],
        keywords=[
            "proposal penelitian",
            "proposal skripsi",
            "usulan penelitian",
            "seminar proposal",
            "sempro",
            "rancangan penelitian",
            "jadwal penelitian",
            "rencana penelitian",
        ],
        max_bab=3,
        requires_front_matter=True,
        has_roman_page_numbers=True,
    ),
    Genre.CUSTOM: GenreBlueprint(
        genre=Genre.CUSTOM,
        name="Dokumen Kustom / Bebas",
        description="Dokumen umum dengan urutan bagian fleksibel.",
        expected_chapters=[
            "PENDAHULUAN",
            "PEMBAHASAN",
            "PENUTUP",
            "DAFTAR PUSTAKA",
        ],
        keywords=[],
        max_bab=0,
        requires_front_matter=False,
        has_roman_page_numbers=False,
    ),
}


class GenreClassificationResult(BaseModel):
    """Result of document genre classification."""

    genre: Genre
    detected_genre: Genre
    confidence: float
    is_manual: bool = False
    markers: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    blueprint: GenreBlueprint


def _roman_to_int(roman_str: str) -> int:
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    val = 0
    s = roman_str.upper().strip()
    for i, c in enumerate(s):
        curr = roman_map.get(c, 0)
        nxt = roman_map.get(s[i + 1], 0) if i + 1 < len(s) else 0
        if curr < nxt:
            val -= curr
        else:
            val += curr
    return val if val > 0 else 0


def classify_genre(ir: IRDocument, hint_genre: str | None = None) -> GenreClassificationResult:
    """Classify the genre of an IRDocument based on structural markers and keywords.

    If hint_genre is provided and valid, it will be applied as manual override,
    while still calculating the detected genre and markers.
    """
    scores: dict[str, float] = {
        Genre.SKRIPSI.value: 1.0,
        Genre.MAKALAH.value: 1.0,
        Genre.LAPORAN_MAGANG.value: 1.0,
        Genre.PROPOSAL_PENELITIAN.value: 1.0,
    }
    markers: list[str] = []

    # 1. Front Matter / Cover Inspection (first 25 paragraphs)
    cover_text = " ".join([p.text.lower() for p in ir.paragraphs[:25]])

    # Regex tests on cover / title
    if re.search(r"\b(proposal\s+(penelitian|skripsi|tesis)|usulan\s+penelitian|seminar\s+proposal)\b", cover_text):
        scores[Genre.PROPOSAL_PENELITIAN.value] += 7.0
        markers.append("Terdeteksi kata kunci 'Proposal Penelitian / Skripsi' pada bagian awal naskah.")

    if re.search(r"\b(laporan\s+(magang|praktik\s+kerja|praktek\s+kerja|pkl|kkn)|kerja\s+praktek)\b", cover_text):
        scores[Genre.LAPORAN_MAGANG.value] += 7.0
        markers.append("Terdeteksi kata kunci 'Laporan Magang / Praktik Kerja' pada bagian awal naskah.")

    if re.search(r"\b(makalah|artikel\s+ilmiah|paper)\b", cover_text):
        scores[Genre.MAKALAH.value] += 6.0
        markers.append("Terdeteksi kata kunci 'Makalah / Paper Ilmiah' pada judul atau awal naskah.")

    if re.search(r"\b(skripsi|tugas\s+akhir|tesis|disertasi)\b", cover_text):
        scores[Genre.SKRIPSI.value] += 5.0
        markers.append("Terdeteksi kata kunci 'Skripsi / Tugas Akhir / Tesis' pada halaman judul.")

    # 2. Heading & Chapter Analysis
    all_heading_texts = [h.text.strip().upper() for h in ir.headings]
    bab_numbers_found: set[int] = set()

    for ht in all_heading_texts:
        match_roman = re.search(r"\bBAB\s+([IVXLCDM]+)\b", ht)
        if match_roman:
            val = _roman_to_int(match_roman.group(1))
            if val > 0:
                bab_numbers_found.add(val)
        else:
            match_digit = re.search(r"\bBAB\s+(\d+)\b", ht)
            if match_digit:
                bab_numbers_found.add(int(match_digit.group(1)))

    if bab_numbers_found:
        max_bab = max(bab_numbers_found)
        markers.append(f"Ditemukan bab berformat formal: {sorted(list(bab_numbers_found))}")

        # If BAB IV & BAB V exist
        if 5 in bab_numbers_found or max_bab >= 5:
            scores[Genre.SKRIPSI.value] += 6.0
            scores[Genre.PROPOSAL_PENELITIAN.value] -= 15.0  # Proposal never reaches BAB V
            markers.append("Naskah memuat hingga BAB V (khas monograf Skripsi lengkap).")
        elif 4 in bab_numbers_found and max_bab == 4:
            scores[Genre.LAPORAN_MAGANG.value] += 5.0
            scores[Genre.SKRIPSI.value] += 2.0
            scores[Genre.PROPOSAL_PENELITIAN.value] -= 10.0
            markers.append("Naskah berakhir di BAB IV.")
        elif max_bab <= 3 and 1 in bab_numbers_found:
            scores[Genre.PROPOSAL_PENELITIAN.value] += 6.0
            markers.append("Struktur bab hanya sampai BAB III (khas Proposal Penelitian).")

        # Makalah typically doesn't use formal "BAB I-V" headings
        scores[Genre.MAKALAH.value] -= 8.0
    else:
        # No formal BAB found
        scores[Genre.MAKALAH.value] += 6.0
        scores[Genre.SKRIPSI.value] -= 4.0
        markers.append("Tidak ditemukan penomoran 'BAB' formal pada heading (khas format Makalah/Paper).")

    # 3. Specific Sections & Structural Markers in Headings
    headings_blob = " ".join(all_heading_texts)
    if "JADWAL PENELITIAN" in headings_blob or "RENCANA PENELITIAN" in headings_blob or "JADWAL KEGIATAN" in headings_blob:
        scores[Genre.PROPOSAL_PENELITIAN.value] += 4.0
        markers.append("Terdapat bagian 'Jadwal Penelitian' / 'Jadwal Kegiatan'.")

    if "INSTANSI" in headings_blob or "PERUSAHAAN" in headings_blob or "GAMBARAN UMUM" in headings_blob or "KEGIATAN MAGANG" in headings_blob:
        scores[Genre.LAPORAN_MAGANG.value] += 4.0
        markers.append("Terdapat bab profil instansi/perusahaan atau aktivitas magang.")

    if "PEMBAHASAN" in headings_blob and not bab_numbers_found:
        scores[Genre.MAKALAH.value] += 3.0
        markers.append("Terdapat bagian 'Pembahasan' secara langsung tanpa format bab.")

    # 4. Pick Best Match
    # Floor negative scores to 0.1
    for k in scores:
        if scores[k] < 0.1:
            scores[k] = 0.1

    detected_str = max(scores, key=lambda k: scores[k])
    detected_genre = Genre(detected_str)

    total_score = sum(scores.values())
    raw_confidence = scores[detected_str] / total_score if total_score > 0 else 0.5
    # Normalize confidence into reasonable 0.60 - 0.98 range
    confidence = round(min(0.98, max(0.60, raw_confidence * 1.3)), 2)

    # Check for manual hint override
    is_manual = False
    applied_genre = detected_genre

    if hint_genre and hint_genre != "auto":
        try:
            applied_genre = Genre(hint_genre.lower())
            is_manual = True
            markers.insert(0, f"Genre ditetapkan secara manual oleh pengguna: '{applied_genre.value}'.")
        except ValueError:
            pass

    blueprint = GENRE_BLUEPRINTS.get(applied_genre, GENRE_BLUEPRINTS[Genre.SKRIPSI])

    return GenreClassificationResult(
        genre=applied_genre,
        detected_genre=detected_genre,
        confidence=1.0 if is_manual else confidence,
        is_manual=is_manual,
        markers=markers,
        scores=scores,
        blueprint=blueprint,
    )

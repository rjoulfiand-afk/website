"""Tests for Multi-Genre Blueprint & Classifier."""

import pytest
from rapikan.classifier.genre import (
    GENRE_BLUEPRINTS,
    Genre,
    GenreClassificationResult,
    classify_genre,
)
from rapikan.ir.schema import IRDocument, Paragraph
from rapikan.rules.campus_profile import DEFAULT_PROFILE, CampusProfile
from rapikan.rules.word.W012_chapter_order import W012ChapterOrder


def _make_para(text: str, para_id: str, is_heading: bool = False, heading_level: int = 1) -> Paragraph:
    return Paragraph(
        id=para_id,
        text=text,
        style_name=f"Heading {heading_level}" if is_heading else "Normal",
        is_heading=is_heading,
        heading_level=heading_level if is_heading else None,
        section_index=0,
    )


def test_classify_skripsi():
    p_title = _make_para("SKRIPSI: SISTEM INFORMASI AKADEMIK BERBASIS WEB", "p_001")
    p_sub = _make_para("Diajukan untuk memenuhi persyaratan gelar Sarjana Komputer", "p_002")
    h1 = _make_para("BAB I PENDAHULUAN", "h_001", is_heading=True)
    h2 = _make_para("BAB II TINJAUAN PUSTAKA", "h_002", is_heading=True)
    h3 = _make_para("BAB III METODE PENELITIAN", "h_003", is_heading=True)
    h4 = _make_para("BAB IV HASIL DAN PEMBAHASAN", "h_004", is_heading=True)
    h5 = _make_para("BAB V PENUTUP DAN KESIMPULAN", "h_005", is_heading=True)
    h_bib = _make_para("DAFTAR PUSTAKA", "h_006", is_heading=True)

    ir = IRDocument(
        paragraphs=[p_title, p_sub, h1, h2, h3, h4, h5, h_bib],
        headings=[h1, h2, h3, h4, h5, h_bib],
    )

    result = classify_genre(ir)
    assert result.genre == Genre.SKRIPSI
    assert result.detected_genre == Genre.SKRIPSI
    assert result.confidence >= 0.75
    assert not result.is_manual
    assert any("BAB V" in m for m in result.markers)


def test_classify_makalah():
    p_title = _make_para("MAKALAH: ETIKA PROFESI DAN TEKNOLOGI INFORMASI", "p_001")
    p_author = _make_para("Disusun Oleh: Kelompok 3", "p_002")
    h1 = _make_para("PENDAHULUAN", "h_001", is_heading=True)
    h2 = _make_para("PEMBAHASAN", "h_002", is_heading=True)
    h3 = _make_para("KESIMPULAN", "h_003", is_heading=True)
    h_bib = _make_para("DAFTAR PUSTAKA", "h_004", is_heading=True)

    ir = IRDocument(
        paragraphs=[p_title, p_author, h1, h2, h3, h_bib],
        headings=[h1, h2, h3, h_bib],
    )

    result = classify_genre(ir)
    assert result.genre == Genre.MAKALAH
    assert result.detected_genre == Genre.MAKALAH
    assert result.confidence >= 0.70
    assert any("Makalah" in m for m in result.markers)


def test_classify_laporan_magang():
    p_title = _make_para("LAPORAN PRAKTIK KERJA LAPANGAN DI PT TELKOM INDONESIA", "p_001")
    p_inst = _make_para("Laporan Magang Industri", "p_002")
    h1 = _make_para("BAB I PENDAHULUAN", "h_001", is_heading=True)
    h2 = _make_para("BAB II GAMBARAN UMUM PERUSAHAAN DAN PROFIL INSTANSI", "h_002", is_heading=True)
    h3 = _make_para("BAB III KEGIATAN MAGANG DAN PELAKSANAAN KERJA", "h_003", is_heading=True)
    h4 = _make_para("BAB IV KESIMPULAN DAN SARAN", "h_004", is_heading=True)
    h_bib = _make_para("DAFTAR PUSTAKA", "h_005", is_heading=True)

    ir = IRDocument(
        paragraphs=[p_title, p_inst, h1, h2, h3, h4, h_bib],
        headings=[h1, h2, h3, h4, h_bib],
    )

    result = classify_genre(ir)
    assert result.genre == Genre.LAPORAN_MAGANG
    assert result.detected_genre == Genre.LAPORAN_MAGANG
    assert result.confidence >= 0.75


def test_classify_proposal_penelitian():
    p_title = _make_para("PROPOSAL PENELITIAN: ANALISIS KEAMANAN JARINGAN", "p_001")
    p_desc = _make_para("Usulan Penelitian Skripsi Program Studi Informatika", "p_002")
    h1 = _make_para("BAB I PENDAHULUAN", "h_001", is_heading=True)
    h2 = _make_para("BAB II TINJAUAN PUSTAKA", "h_002", is_heading=True)
    h3 = _make_para("BAB III METODOLOGI PENELITIAN", "h_003", is_heading=True)
    h_jadwal = _make_para("JADWAL PENELITIAN", "h_004", is_heading=True)
    h_bib = _make_para("DAFTAR PUSTAKA", "h_005", is_heading=True)

    ir = IRDocument(
        paragraphs=[p_title, p_desc, h1, h2, h3, h_jadwal, h_bib],
        headings=[h1, h2, h3, h_jadwal, h_bib],
    )

    result = classify_genre(ir)
    assert result.genre == Genre.PROPOSAL_PENELITIAN
    assert result.detected_genre == Genre.PROPOSAL_PENELITIAN
    assert result.confidence >= 0.75
    assert any("Proposal" in m for m in result.markers)


def test_manual_hint_override():
    # Document looks like makalah, but user manually insists on skripsi
    p_title = _make_para("MAKALAH TENTANG KECERDASAN BUATAN", "p_001")
    h1 = _make_para("PENDAHULUAN", "h_001", is_heading=True)
    ir = IRDocument(paragraphs=[p_title, h1], headings=[h1])

    result = classify_genre(ir, hint_genre="skripsi")
    assert result.genre == Genre.SKRIPSI
    assert result.detected_genre == Genre.MAKALAH
    assert result.is_manual is True
    assert result.confidence == 1.0


def test_profile_with_genre():
    base_profile = CampusProfile()
    assert base_profile.genre == "skripsi"
    assert "BAB V" in base_profile.chapter_order.chapters

    makalah_profile = base_profile.with_genre(Genre.MAKALAH)
    assert makalah_profile.genre == "makalah"
    assert "PEMBAHASAN" in makalah_profile.chapter_order.chapters
    assert "BAB V" not in makalah_profile.chapter_order.chapters

    prop_profile = base_profile.with_genre("proposal_penelitian")
    assert prop_profile.genre == "proposal_penelitian"
    assert "JADWAL PENELITIAN" in prop_profile.chapter_order.chapters
    assert "BAB V" not in prop_profile.chapter_order.chapters


def test_w012_adapts_to_genre():
    rule = W012ChapterOrder()

    # 1. Makalah with correct order
    h1 = _make_para("PENDAHULUAN", "h1", is_heading=True)
    h2 = _make_para("PEMBAHASAN", "h2", is_heading=True)
    h3 = _make_para("KESIMPULAN", "h3", is_heading=True)
    h_bib = _make_para("DAFTAR PUSTAKA", "h4", is_heading=True)
    ir_clean = IRDocument(paragraphs=[h1, h2, h3, h_bib], headings=[h1, h2, h3, h_bib])

    profile_makalah = DEFAULT_PROFILE.with_genre(Genre.MAKALAH)
    findings = rule.check(ir_clean, profile_makalah)
    assert len(findings) == 0  # No violation for makalah!

    # 2. Makalah with wrong order: Pembahasan before Pendahuluan
    ir_wrong = IRDocument(paragraphs=[h2, h1, h3, h_bib], headings=[h2, h1, h3, h_bib])
    findings_wrong = rule.check(ir_wrong, profile_makalah)
    assert len(findings_wrong) >= 1
    assert findings_wrong[0].rule_id == "W012"
    assert "makalah" in findings_wrong[0].evidence.detail

    # 3. Proposal with BAB I - III + Jadwal (valid for proposal, without BAB IV/V)
    p_b1 = _make_para("BAB I PENDAHULUAN", "p1", is_heading=True)
    p_b2 = _make_para("BAB II LANDASAN TEORI", "p2", is_heading=True)
    p_b3 = _make_para("BAB III METODOLOGI PENELITIAN", "p3", is_heading=True)
    p_jadwal = _make_para("JADWAL PENELITIAN", "p4", is_heading=True)
    p_bib = _make_para("DAFTAR PUSTAKA", "p5", is_heading=True)
    ir_prop = IRDocument(paragraphs=[p_b1, p_b2, p_b3, p_jadwal, p_bib], headings=[p_b1, p_b2, p_b3, p_jadwal, p_bib])

    profile_prop = DEFAULT_PROFILE.with_genre(Genre.PROPOSAL_PENELITIAN)
    findings_prop = rule.check(ir_prop, profile_prop)
    assert len(findings_prop) == 0

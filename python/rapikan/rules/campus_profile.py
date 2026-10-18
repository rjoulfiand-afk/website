"""Campus profile: holds all rule thresholds.

This is the single source of truth for campus-specific formatting requirements.
Rules MUST NOT hardcode threshold values.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MarginProfile(BaseModel):
    top_cm: float = 4.0
    bottom_cm: float = 3.0
    left_cm: float = 4.0
    right_cm: float = 3.0


class FontProfile(BaseModel):
    name: str = "Times New Roman"
    size_pt: float = 12.0


class SpacingProfile(BaseModel):
    line_spacing_value: float = 240.0  # in twips (auto rule)
    line_spacing_rule: str = "auto"
    space_before_pt: float = 0.0
    space_after_pt: float = 0.0


class ChapterOrder(BaseModel):
    """Expected chapter/section order."""
    chapters: list[str] = Field(
        default_factory=lambda: [
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
        ]
    )


class FrontMatterFormat(BaseModel):
    """Expected front-matter section formatting."""
    font_name: str = "Times New Roman"
    font_size_pt: float = 12.0
    alignment: str = "center"


class CampusProfile(BaseModel):
    """All thresholds and requirements for a campus."""

    slug: str = "default"
    name: str = "Default Campus"
    source_document: str | None = None
    guideline_year: int | None = None
    verified: bool = False

    margin: MarginProfile = Field(default_factory=MarginProfile)
    body_font: FontProfile = Field(default_factory=FontProfile)
    heading_font: FontProfile = Field(
        default_factory=lambda: FontProfile(name="Times New Roman", size_pt=12.0)
    )
    body_spacing: SpacingProfile = Field(default_factory=SpacingProfile)
    chapter_order: ChapterOrder = Field(default_factory=ChapterOrder)
    front_matter_format: FrontMatterFormat = Field(default_factory=FrontMatterFormat)

    # Document Genre (skripsi, makalah, laporan_magang, proposal_penelitian, custom)
    genre: str = "skripsi"

    # W001 thresholds: font size above which Normal-styled bold para is "fake heading"
    fake_heading_min_size_pt: float = 13.0

    # W010: double space check
    check_double_space: bool = True

    # W002: manual numbering patterns to detect
    manual_numbering_patterns: list[str] = Field(
        default_factory=lambda: [
            r"^\d+\.\s",        # "1. "
            r"^[a-z]\.\s",      # "a. "
            r"^\([a-z]\)\s",    # "(a) "
            r"^\(\d+\)\s",      # "(1) "
        ]
    )

    def with_genre(self, genre_val: Any) -> CampusProfile:
        """Return a copy of the profile configured with the specified genre blueprint."""
        from rapikan.classifier.genre import GENRE_BLUEPRINTS, Genre

        g = Genre(genre_val.value if hasattr(genre_val, "value") else str(genre_val).lower())
        new_profile = self.model_copy(deep=True)
        new_profile.genre = g.value

        if g in GENRE_BLUEPRINTS:
            bp = GENRE_BLUEPRINTS[g]
            new_profile.chapter_order = ChapterOrder(chapters=list(bp.expected_chapters))

        return new_profile


# Default profile (override per campus)
DEFAULT_PROFILE = CampusProfile()



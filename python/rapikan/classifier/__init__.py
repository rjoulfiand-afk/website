"""Rapikan document classifier package."""

from rapikan.classifier.genre import (
    GENRE_BLUEPRINTS,
    Genre,
    GenreBlueprint,
    GenreClassificationResult,
    classify_genre,
)

__all__ = [
    "Genre",
    "GenreBlueprint",
    "GENRE_BLUEPRINTS",
    "GenreClassificationResult",
    "classify_genre",
]

"""Twip/cm conversion helpers and comparison utilities."""

CM_PER_INCH = 2.54
TWIPS_PER_INCH = 1440
TWIPS_PER_CM = TWIPS_PER_INCH / CM_PER_INCH  # ≈ 566.929


def twips_to_cm(twips: int | float) -> float:
    """Convert twips to centimetres."""
    return twips / TWIPS_PER_CM


def cm_to_twips(cm: float) -> int:
    """Convert centimetres to twips (rounded to nearest integer)."""
    return round(cm * TWIPS_PER_CM)


def twips_approx_equal(a: int | float, b: int | float, tolerance: int = 2) -> bool:
    """Return True if two twip values are within *tolerance* twips of each other."""
    return abs(a - b) <= tolerance


def halfpt_to_pt(half_pts: int | float) -> float:
    """Convert half-points (docx w:sz) to points."""
    return half_pts / 2.0


def pt_to_halfpt(pts: float) -> int:
    """Convert points to half-points."""
    return round(pts * 2)


def twips_to_pt(twips: int | float) -> float:
    """Convert twips (twentieths-of-a-point) to points."""
    return twips / 20.0


def pt_to_twips(pts: float) -> int:
    """Convert points to twips (twentieths-of-a-point)."""
    return round(pts * 20)

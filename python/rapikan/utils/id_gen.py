"""Paragraph / element ID generator."""

import itertools


def make_id_generator(prefix: str = "p") -> "callable[[], str]":
    """Return a callable that yields sequential IDs like p_0001, p_0002, …"""
    counter = itertools.count(1)

    def _next() -> str:
        return f"{prefix}_{next(counter):04d}"

    return _next


def sequential_ids(prefix: str = "p", start: int = 1):
    """Infinite generator of sequential IDs."""
    n = start
    while True:
        yield f"{prefix}_{n:04d}"
        n += 1

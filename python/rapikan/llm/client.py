"""LLM client ABC and FakeLLMClient for testing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def complete(self, prompt: str, **kwargs: Any) -> str:
        """Send a prompt and return the completion string."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the LLM service is reachable."""
        ...


class FakeLLMClient(LLMClient):
    """Deterministic fake LLM client for testing.

    Records calls and returns preset responses.
    """

    def __init__(self, responses: dict[str, str] | None = None):
        self._responses = responses or {}
        self.calls: list[str] = []

    def complete(self, prompt: str, **kwargs: Any) -> str:
        self.calls.append(prompt)
        # Return first matching preset or empty string
        for key, val in self._responses.items():
            if key in prompt:
                return val
        return ""

    def is_available(self) -> bool:
        return True

"""Finding (result) schema for Rapikan rules."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class LocationType(str, Enum):
    PARAGRAPH = "paragraph"
    TABLE_CELL = "table_cell"
    TABLE = "table"
    SECTION = "section"
    DOCUMENT = "document"


class Location(BaseModel):
    type: LocationType
    id: str  # paragraph id, cell address, "doc", etc.
    label: str  # human-readable label, e.g. "Paragraf p_0012"
    page_estimate: int | None = None
    page_is_estimate: bool = True
    section_index: int | None = None


class Evidence(BaseModel):
    snippet: str  # text excerpt triggering the finding
    detail: str | None = None  # additional machine-readable detail
    extra: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    rule_id: str
    rule_name: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    location: Location
    evidence: Evidence
    auto_fixable: bool = False
    changes_text: bool = False  # If True: cannot run in batch, requires individual proposal approval
    suggestion: str
    guide_module_slug: str | None = None
    llm_source: bool = False
    requires_llm: bool = False

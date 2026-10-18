"""Rule registry: auto-discover and filter rules."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Type

from rapikan.rules.base import BaseRule


def _discover_rules(package_path: str) -> list[Type[BaseRule]]:
    """Recursively import all modules under *package_path* and collect BaseRule subclasses."""
    rules: list[Type[BaseRule]] = []
    package = importlib.import_module(package_path)
    prefix = package.__name__ + "."

    for _finder, name, _is_pkg in pkgutil.walk_packages(
        path=package.__path__,
        prefix=prefix,
        onerror=lambda x: None,
    ):
        mod = importlib.import_module(name)
        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseRule)
                and obj is not BaseRule
                and obj.rule_id  # must have a non-empty rule_id
            ):
                rules.append(obj)

    return rules


class RuleRegistry:
    """Manages all known rules and filters them by phase/llm requirements."""

    def __init__(self):
        self._rules: list[Type[BaseRule]] = []

    def load_all(self) -> None:
        """Auto-discover all rules in rapikan.rules.word and rapikan.rules.cross."""
        discovered: list[Type[BaseRule]] = []
        for pkg in ("rapikan.rules.word", "rapikan.rules.cross"):
            try:
                discovered.extend(_discover_rules(pkg))
            except ModuleNotFoundError:
                pass
        # Deduplicate by rule_id
        seen: set[str] = set()
        for r in discovered:
            if r.rule_id not in seen:
                self._rules.append(r)
                seen.add(r.rule_id)

    def register(self, rule_cls: Type[BaseRule]) -> None:
        """Manually register a rule class."""
        if not any(r.rule_id == rule_cls.rule_id for r in self._rules):
            self._rules.append(rule_cls)

    def get_rules(
        self,
        phase: int | None = None,
        include_llm: bool = False,
        include_render: bool = False,
    ) -> list[BaseRule]:
        """Return instantiated rule objects filtered by criteria."""
        result = []
        for cls in self._rules:
            if phase is not None and cls.phase != phase:
                continue
            if cls.requires_llm and not include_llm:
                continue
            if cls.requires_render and not include_render:
                continue
            result.append(cls())
        return result

    @property
    def all_rule_ids(self) -> list[str]:
        return [r.rule_id for r in self._rules]

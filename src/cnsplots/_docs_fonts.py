"""Helpers for deterministic docs font selection."""

from __future__ import annotations

from collections.abc import Iterable

from cnsplots._settings import settings


def _dedupe_font_names(font_names: Iterable[str]) -> tuple[str, ...]:
    """Return font names in order, skipping blanks and duplicates."""
    seen: set[str] = set()
    ordered: list[str] = []
    for font_name in font_names:
        normalized = font_name.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def apply_docs_font_override(docs_font: str | None) -> None:
    """Pin a docs-only sans-serif font without changing package defaults."""
    normalized_docs_font = (docs_font or "").strip()
    if not normalized_docs_font:
        return

    settings.font_sans_serif = _dedupe_font_names(
        [
            normalized_docs_font,
            "Helvetica",
            "Helvetica Neue",
            "Arial",
            *settings.font_sans_serif,
        ]
    )
    settings.panel_label_fontname = normalized_docs_font

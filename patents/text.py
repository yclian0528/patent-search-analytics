"""Shared text normalization utilities for patent data and queries."""

import unicodedata


def normalize_text(text: str | None) -> str:
    """Normalize character width, case, and whitespace while preserving punctuation."""
    if text is None:
        return ""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(normalized.split())

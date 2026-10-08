"""Patent search query definitions and filtering rules.

This module receives data prepared by ``patents.data``. It does not load files
or depend on Streamlit.
"""

import re
from dataclasses import dataclass
from datetime import date

import pandas as pd

from .text import normalize_text


# Fields searched by keyword.
KEYWORD_COLUMNS = ("_title", "_title_en", "_abstract", "_patent_no")
# Fields required for filtering.
REQUIRED_COLUMNS = {
    *KEYWORD_COLUMNS,
    "type",
    "_applicants",
    "_applicants_en",
    "_ipc",
    "_publication_date",
}


@dataclass(frozen=True)
class SearchQuery:
    """Search conditions supplied by the UI or another caller."""

    keyword: str = ""
    patent_types: tuple[str, ...] = ()
    applicants: tuple[str, ...] = ()
    ipc_prefixes: tuple[str, ...] = ()
    publication_start: date | None = None
    publication_end: date | None = None


def parse_keywords(value: str) -> tuple[str, ...]:
    """Return unique normalized keywords separated by commas."""
    normalized = normalize_text(value)
    if not normalized:
        return ()

    words = (word.strip() for word in re.split(r"[,，]+", normalized))
    return tuple(dict.fromkeys(word for word in words if word))


def validate_query(query: SearchQuery) -> None:
    """Raise ValueError when the query contains an invalid date range."""
    if (
        query.publication_start is not None
        and query.publication_end is not None
        and query.publication_start > query.publication_end
    ):
        raise ValueError("Publication start date cannot be later than the end date.")


def _validate_dataframe(patents: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(patents.columns)
    if missing:
        raise ValueError(
            f"Patent data is not prepared; missing fields: {', '.join(sorted(missing))}"
        )


def _keyword_mask(patents: pd.DataFrame, keyword: str) -> pd.Series:
    """Match one keyword in any searchable field."""
    matches = pd.Series(False, index=patents.index, dtype=bool)
    for column in KEYWORD_COLUMNS:
        matches |= patents[column].str.contains(keyword, regex=False, na=False)
    return matches


def _normalize_ipc_prefix(value: str) -> str:
    return normalize_text(value).replace(" ", "").upper()


def filter_patents(patents: pd.DataFrame, query: SearchQuery) -> pd.DataFrame:
    """Return a copy containing patents that match all active conditions.

    Keywords are combined with AND, while selections within the same filter
    are combined with OR. Date boundaries are inclusive.
    """
    _validate_dataframe(patents)
    validate_query(query)

    mask = pd.Series(True, index=patents.index, dtype=bool)

    # Every keyword must match at least one searchable field.
    for keyword in parse_keywords(query.keyword):
        mask &= _keyword_mask(patents, keyword)

    if query.patent_types:
        mask &= patents["type"].isin(query.patent_types)

    if query.applicants:
        selected_applicants = {
            normalized
            for applicant in query.applicants
            if (normalized := normalize_text(applicant))
        }
        mask &= pd.Series(
            (
                bool(selected_applicants.intersection(names_zh))
                or bool(selected_applicants.intersection(names_en))
                for names_zh, names_en in zip(
                    patents["_applicants"], patents["_applicants_en"]
                )
            ),
            index=patents.index,
            dtype=bool,
        )

    if query.ipc_prefixes:
        prefixes = tuple(
            normalized
            for prefix in query.ipc_prefixes
            if (normalized := _normalize_ipc_prefix(prefix))
        )
        mask &= patents["_ipc"].map(
            lambda codes: any(
                code.startswith(prefix) for code in codes for prefix in prefixes
            )
        )

    if query.publication_start is not None:
        mask &= patents["_publication_date"] >= pd.Timestamp(query.publication_start)

    if query.publication_end is not None:
        mask &= patents["_publication_date"] <= pd.Timestamp(query.publication_end)

    return patents.loc[mask].copy()

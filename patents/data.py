"""Initialize patent data for search and filtering.

This module loads and validates the source JSON, prepares searchable fields,
and builds metadata for UI filters. It does not run searches or render the UI.

Run ``python -m patents.data`` from the project root to inspect the metadata.
"""

import json
from pathlib import Path

import pandas as pd

from .text import normalize_text


DEFAULT_DATA_PATH = Path(__file__).resolve().parents[1] / "data/raw/patents.json"
# Text fields normalized for keyword search.
TEXT_FIELDS = ("title", "title_en", "abstract", "patent_no")
# Date fields parsed for range filtering.
DATE_FIELDS = ("application_date", "publication_date")
# List fields used for applicant and IPC filtering.
ARRAY_FIELDS = ("applicants", "applicants_en", "ipc")


def load_patents(path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Load and validate the source JSON as a DataFrame."""
    with Path(path).open(encoding="utf-8-sig") as file:
        records = json.load(file)
    if not isinstance(records, list) or not records:
        raise ValueError("Patent data must be a non-empty JSON array.")
    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Each patent record must be a JSON object.")
    return pd.DataFrame(records)


def prepare_patents(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with validated and normalized search fields."""
    required = {*TEXT_FIELDS, *DATE_FIELDS, *ARRAY_FIELDS, "type"}
    missing = required - set(raw_df.columns)
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(sorted(missing))}")

    df = raw_df.copy(deep=True)
    if df["patent_no"].isna().any() or df["patent_no"].duplicated().any():
        raise ValueError("Patent numbers must be present and unique.")

    # Validate list fields; use [] for missing values.
    for field in ARRAY_FIELDS:
        valid = df[field].map(
            lambda values: isinstance(values, list)
            and all(isinstance(value, str) for value in values)
        )
        if not valid.all():
            raise ValueError(f"{field} must be a list of strings; use [] if empty.")

    # Validate dates and create datetime columns.
    for field in DATE_FIELDS:
        parsed = pd.to_datetime(df[field], format="%Y-%m-%d", errors="coerce")
        if parsed.isna().any():
            raise ValueError(f"{field} contains missing or invalid dates.")
        df[f"_{field}"] = parsed
    if (df["_application_date"] > df["_publication_date"]).any():
        raise ValueError("Application dates cannot be later than publication dates.")

    # Normalize search text while preserving source fields for display and analysis.
    for field in TEXT_FIELDS:
        df[f"_{field}"] = df[field].fillna("").map(normalize_text)
    for field in ("applicants", "applicants_en"):
        df[f"_{field}"] = df[field].map(
            lambda names: [normalize_text(name) for name in names]
        )
    df["_ipc"] = df["ipc"].map(
        lambda codes: [normalize_text(code).replace(" ", "").upper() for code in codes]
    )
    return df


def build_metadata(df: pd.DataFrame, original_columns: list[str]) -> dict:
    """Build dataset metadata and filter options."""
    metadata = {
        "columns": list(original_columns),
        "total_count": len(df),
        "patent_types": sorted(df["type"].dropna().unique().tolist()),
        "ipc_prefixes": sorted({code[:4] for codes in df["_ipc"] for code in codes}),
    }
    for field in DATE_FIELDS:
        metadata[f"{field}_min"] = df[f"_{field}"].min().date()
        metadata[f"{field}_max"] = df[f"_{field}"].max().date()
    return metadata


def initialize_data(path: str | Path = DEFAULT_DATA_PATH) -> tuple[pd.DataFrame, dict]:
    """Return prepared patent data and dataset metadata."""
    raw_df = load_patents(path)
    prepared_df = prepare_patents(raw_df)
    metadata = build_metadata(prepared_df, raw_df.columns.tolist())
    return prepared_df, metadata


if __name__ == "__main__":
    patents_df, metadata = initialize_data()
    print(json.dumps(metadata, ensure_ascii=False, indent=2, default=str))

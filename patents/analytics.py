"""Statistical summaries for a complete or filtered patent dataset."""

import pandas as pd


def _require_columns(patents: pd.DataFrame, required: set[str]) -> None:
    missing = required - set(patents.columns)
    if missing:
        raise ValueError(
            f"Patent data is not prepared; missing fields: {', '.join(sorted(missing))}"
        )


def _validate_top_n(top_n: int | None) -> None:
    if top_n is not None and top_n < 1:
        raise ValueError("top_n must be a positive integer or None.")


def applicant_ranking(
    patents: pd.DataFrame, top_n: int | None = 10
) -> pd.DataFrame:
    """Count patents per Chinese applicant and return a deterministic ranking.

    A patent is counted at most once for each applicant. Joint applications
    count once toward every listed applicant.
    """
    _require_columns(patents, {"patent_no", "applicants"})
    _validate_top_n(top_n)

    columns = ["applicant", "patent_count"]
    if patents.empty:
        return pd.DataFrame(columns=columns)

    expanded = patents[["patent_no", "applicants"]].explode("applicants")
    expanded = expanded.dropna(subset=["applicants"])
    expanded = expanded.loc[expanded["applicants"] != ""]
    expanded = expanded.drop_duplicates(["patent_no", "applicants"])

    ranking = (
        expanded.groupby("applicants")["patent_no"]
        .nunique()
        .rename("patent_count")
        .reset_index()
        .rename(columns={"applicants": "applicant"})
        .sort_values(
            ["patent_count", "applicant"],
            ascending=[False, True],
            kind="stable",
        )
        .reset_index(drop=True)
    )
    return ranking.head(top_n).reset_index(drop=True) if top_n else ranking


def yearly_trend(patents: pd.DataFrame) -> pd.DataFrame:
    """Count patents by publication year in ascending year order."""
    _require_columns(patents, {"_publication_date"})

    columns = ["publication_year", "patent_count"]
    if patents.empty:
        return pd.DataFrame(columns=columns)

    trend = (
        patents["_publication_date"]
        .dt.year.value_counts()
        .sort_index()
        .rename_axis("publication_year")
        .rename("patent_count")
        .reset_index()
    )
    return trend[columns]


def ipc_distribution(
    patents: pd.DataFrame, top_n: int | None = 10
) -> pd.DataFrame:
    """Count patents by four-character IPC prefix.

    A patent is counted at most once per prefix, even when it contains multiple
    IPC codes with the same prefix. Patents without IPC data are excluded.
    """
    _require_columns(patents, {"patent_no", "_ipc"})
    _validate_top_n(top_n)

    columns = ["ipc_prefix", "patent_count"]
    if patents.empty:
        return pd.DataFrame(columns=columns)

    expanded = patents[["patent_no", "_ipc"]].explode("_ipc")
    expanded = expanded.dropna(subset=["_ipc"])
    expanded = expanded.loc[expanded["_ipc"] != ""].copy()
    expanded["ipc_prefix"] = expanded["_ipc"].str[:4]
    expanded = expanded.drop_duplicates(["patent_no", "ipc_prefix"])

    distribution = (
        expanded.groupby("ipc_prefix")["patent_no"]
        .nunique()
        .rename("patent_count")
        .reset_index()
        .sort_values(
            ["patent_count", "ipc_prefix"],
            ascending=[False, True],
            kind="stable",
        )
        .reset_index(drop=True)
    )
    return distribution.head(top_n).reset_index(drop=True) if top_n else distribution

"""Streamlit interface for patent search and browsing."""

from pathlib import Path

import pandas as pd
import streamlit as st

from patents.data import DEFAULT_DATA_PATH, initialize_data
from patents.search import SearchQuery, filter_patents


TYPE_LABELS = {
    "invention": "發明",
    "model": "新型",
    "design": "設計",
}


@st.cache_data(show_spinner="正在載入專利資料…", max_entries=2)
def get_app_data(path: str, file_version: tuple[int, int]):
    """Load prepared data and invalidate the cache when the source file changes."""
    return initialize_data(path)


def render_search_form(metadata: dict) -> SearchQuery:
    """Render search controls and return their current values as a query."""
    st.sidebar.header("檢索條件")

    with st.sidebar.form("search_form"):
        keyword = st.text_input(
            "關鍵字",
            placeholder="例如：半導體封裝, 製造方法",
            help="多個關鍵字請以逗號分隔；所有關鍵字都必須符合。",
        )
        patent_types = st.multiselect(
            "專利類型",
            options=metadata["patent_types"],
            format_func=lambda value: TYPE_LABELS.get(value, value),
            placeholder="全部類型",
        )
        applicants = st.multiselect(
            "申請人",
            options=metadata["applicant_options"],
            placeholder="輸入名稱以搜尋",
        )
        ipc_prefixes = st.multiselect(
            "IPC 分類",
            options=metadata["ipc_prefixes"],
            placeholder="例如：H01L",
        )
        publication_start = st.date_input(
            "公告日起日",
            value=metadata["publication_date_min"],
            min_value=metadata["publication_date_min"],
            max_value=metadata["publication_date_max"],
            format="YYYY/MM/DD",
        )
        publication_end = st.date_input(
            "公告日迄日",
            value=metadata["publication_date_max"],
            min_value=metadata["publication_date_min"],
            max_value=metadata["publication_date_max"],
            format="YYYY/MM/DD",
        )
        st.form_submit_button("搜尋", type="primary", width="stretch")

    return SearchQuery(
        keyword=keyword,
        patent_types=tuple(patent_types),
        applicants=tuple(applicants),
        ipc_prefixes=tuple(ipc_prefixes),
        publication_start=publication_start,
        publication_end=publication_end,
    )


def build_result_table(results: pd.DataFrame) -> pd.DataFrame:
    """Create a read-only result table without changing the search results."""
    ordered = results.sort_values(
        ["_publication_date", "patent_no"], ascending=[False, True]
    )
    table = ordered[
        ["patent_no", "title", "type", "applicants", "publication_date", "main_ipc"]
    ].copy()
    table["type"] = table["type"].map(TYPE_LABELS).fillna(table["type"])
    table["applicants"] = table["applicants"].map(lambda names: "、".join(names))
    table["main_ipc"] = table["main_ipc"].fillna("未提供")
    return table.rename(
        columns={
            "patent_no": "公告號",
            "title": "專利名稱",
            "type": "類型",
            "applicants": "申請人",
            "publication_date": "公告日",
            "main_ipc": "主要 IPC",
        }
    )


def format_value(value) -> str:
    """Format a source value for display without changing stored data."""
    if isinstance(value, list):
        return "、".join(value) if value else "未提供"
    if value is None or pd.isna(value) or value == "":
        return "未提供"
    return str(value)


def get_selected_patent_no(
    result_table: pd.DataFrame, selected_rows: list[int]
) -> str:
    """Map a selected display row to a patent number, defaulting to the first row."""
    position = selected_rows[0] if selected_rows else 0
    if position < 0 or position >= len(result_table):
        position = 0
    return str(result_table.iloc[position]["公告號"])


def render_patent_detail(results: pd.DataFrame, selected_no: str) -> None:
    """Render the complete record for one patent in the current results."""
    st.subheader("專利詳情")
    patent = results.loc[results["patent_no"] == selected_no].iloc[0]

    st.markdown(f"### {format_value(patent['title'])}")
    if format_value(patent["title_en"]) != "未提供":
        st.caption(format_value(patent["title_en"]))

    basic_left, basic_right = st.columns(2)
    with basic_left:
        st.markdown(f"**公告號：** {format_value(patent['patent_no'])}")
        st.markdown(f"**證書號：** {format_value(patent['certificate_no'])}")
        st.markdown(f"**申請號：** {format_value(patent['application_no'])}")
        st.markdown(
            f"**專利類型：** {TYPE_LABELS.get(patent['type'], patent['type'])}"
        )
    with basic_right:
        st.markdown(f"**申請日：** {format_value(patent['application_date'])}")
        st.markdown(f"**公告日：** {format_value(patent['publication_date'])}")
        st.markdown(f"**主要 IPC：** {format_value(patent['main_ipc'])}")
        st.markdown(f"**全部 IPC：** {format_value(patent['ipc'])}")

    st.markdown("**申請人：**")
    st.write(format_value(patent["applicants"]))
    st.markdown("**英文申請人：**")
    st.write(format_value(patent["applicants_en"]))
    st.markdown("**發明人：**")
    st.write(format_value(patent["inventors"]))
    st.markdown("**摘要：**")
    st.write(format_value(patent["abstract"]))
    st.markdown(f"**羅卡諾分類：** {format_value(patent['locarno'])}")


def load_data_or_stop(path: Path) -> tuple[pd.DataFrame, dict]:
    """Load app data and show a user-facing error if initialization fails."""
    try:
        stat = path.stat()
        return get_app_data(str(path), (stat.st_mtime_ns, stat.st_size))
    except (OSError, ValueError) as error:
        st.error(f"無法載入專利資料：{error}")
        st.stop()


def main() -> None:
    st.set_page_config(page_title="專利檢索分析", page_icon="🔎", layout="wide")
    st.title("專利檢索分析")
    st.caption("搜尋台灣公告專利，並依類型、申請人、公告日期與 IPC 分類篩選。")

    patents, metadata = load_data_or_stop(DEFAULT_DATA_PATH)
    query = render_search_form(metadata)

    try:
        results = filter_patents(patents, query)
    except ValueError as error:
        st.error(f"查詢條件錯誤：{error}")
        st.stop()

    st.metric("符合條件的專利", len(results))
    if results.empty:
        st.info("找不到符合條件的專利，請調整檢索條件。")
        return

    st.subheader("檢索結果")
    st.caption("表格內容僅供檢視；勾選任一列可在下方查看完整資料。")
    result_table = build_result_table(results)
    selection = st.dataframe(
        result_table,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        key="patent_result_table",
    )
    selected_no = get_selected_patent_no(result_table, selection.selection.rows)
    st.divider()
    render_patent_detail(results, selected_no)


if __name__ == "__main__":
    main()

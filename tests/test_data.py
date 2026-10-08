"""Tests for patent data loading and preparation."""

import unittest
from datetime import date

from patents.data import build_metadata, initialize_data, load_patents, prepare_patents
from patents.text import normalize_text


class DataInitializationTests(unittest.TestCase):
    def test_real_dataset_metadata_and_all_ipc(self):
        df, metadata = initialize_data()
        self.assertEqual(metadata["total_count"], 485)
        self.assertEqual(len(metadata["columns"]), 15)
        self.assertEqual(set(metadata["patent_types"]), {"invention", "model", "design"})
        self.assertEqual(metadata["publication_date_min"], date(2022, 1, 1))
        self.assertEqual(metadata["publication_date_max"], date(2026, 9, 11))
        self.assertIn("台灣積體電路製造股份有限公司", metadata["applicant_options"])
        self.assertIn("WELTREND SEMICONDUCTOR INC.", metadata["applicant_options"])
        self.assertIn("H01L", metadata["ipc_prefixes"])
        self.assertEqual(
            sum(any(c.startswith("H01L") for c in codes) for codes in df["_ipc"]),
            150,
        )

    def test_original_data_and_missing_values_are_preserved(self):
        raw = load_patents()
        before = raw.copy(deep=True)
        prepared = prepare_patents(raw)
        self.assertTrue(raw.equals(before))
        self.assertTrue(prepared[raw.columns].equals(raw))
        self.assertEqual(
            prepared.loc[prepared["abstract"].isna(), "_abstract"].unique().tolist(),
            [""],
        )
        self.assertTrue(
            prepared.loc[prepared["type"] == "design", "_ipc"]
            .map(lambda codes: codes == [])
            .all()
        )

    def test_normalization_preserves_punctuation(self):
        self.assertEqual(normalize_text("  ＬＥＤ　（Ａ＋Ｂ）\n晶片  "), "led (a+b) 晶片")
        self.assertEqual(normalize_text(None), "")

    def test_invalid_date_fails_with_field_name(self):
        raw = load_patents().head(1).copy()
        raw.loc[raw.index[0], "publication_date"] = "2026-02-30"
        with self.assertRaisesRegex(ValueError, "publication_date"):
            prepare_patents(raw)

    def test_options_include_applicants_and_secondary_ipc(self):
        raw = load_patents().head(1).copy()
        raw.at[raw.index[0], "applicants"] = ["Applicant B", "Applicant A"]
        raw.at[raw.index[0], "applicants_en"] = []
        raw.at[raw.index[0], "ipc"] = ["G06F001/26", "H01L023/488"]
        metadata = build_metadata(prepare_patents(raw), raw.columns.tolist())
        self.assertEqual(metadata["applicant_options"], ["Applicant A", "Applicant B"])
        self.assertEqual(metadata["ipc_prefixes"], ["G06F", "H01L"])


if __name__ == "__main__":
    unittest.main()

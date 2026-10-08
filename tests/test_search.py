"""Tests for patent search rules using the supplied dataset."""

import unittest
from datetime import date

import pandas as pd

from patents.data import initialize_data
from patents.search import SearchQuery, filter_patents, parse_keywords


class PatentSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patents, _ = initialize_data()

    def test_keyword_parser_normalizes_separators_and_removes_duplicates(self):
        self.assertEqual(
            parse_keywords(" 半導體, 封裝，半導體, 製程　方法 "),
            ("半導體", "封裝", "製程 方法"),
        )

    def test_spaces_inside_a_keyword_are_preserved(self):
        patents = self.patents.head(2).copy(deep=True)
        patents["_title"] = ["power supply controller", "power control and supply"]
        for column in ("_title_en", "_abstract", "_patent_no"):
            patents[column] = ""

        phrase_result = filter_patents(patents, SearchQuery(keyword="power supply"))
        word_result = filter_patents(patents, SearchQuery(keyword="power, supply"))

        self.assertEqual(phrase_result.index.tolist(), [patents.index[0]])
        self.assertEqual(word_result.index.tolist(), patents.index.tolist())

    def test_empty_query_returns_a_copy_of_all_patents(self):
        result = filter_patents(self.patents, SearchQuery())
        self.assertEqual(len(result), 485)
        self.assertIsNot(result, self.patents)

    def test_type_filter(self):
        result = filter_patents(
            self.patents,
            SearchQuery(patent_types=("design",)),
        )
        self.assertEqual(len(result), 80)
        self.assertEqual(set(result["type"]), {"design"})

    def test_multiple_values_in_one_filter_use_or(self):
        result = filter_patents(
            self.patents,
            SearchQuery(patent_types=("invention", "model")),
        )
        self.assertEqual(len(result), 405)
        self.assertEqual(set(result["type"]), {"invention", "model"})

    def test_applicant_filter(self):
        result = filter_patents(
            self.patents,
            SearchQuery(applicants=("台灣積體電路製造股份有限公司",)),
        )
        self.assertEqual(len(result), 22)

    def test_english_applicant_filter(self):
        result = filter_patents(
            self.patents,
            SearchQuery(applicants=("WELTREND SEMICONDUCTOR INC.",)),
        )
        self.assertEqual(len(result), 1)

    def test_ipc_prefix_checks_all_ipc_codes(self):
        result = filter_patents(
            self.patents,
            SearchQuery(ipc_prefixes=("h01l",)),
        )
        self.assertEqual(len(result), 150)

    def test_keyword_search_handles_full_width_characters(self):
        half_width = filter_patents(self.patents, SearchQuery(keyword="LED"))
        full_width = filter_patents(self.patents, SearchQuery(keyword="ＬＥＤ"))
        self.assertGreater(len(half_width), 0)
        self.assertEqual(half_width.index.tolist(), full_width.index.tolist())

    def test_publication_date_range_is_inclusive(self):
        result = filter_patents(
            self.patents,
            SearchQuery(
                publication_start=date(2026, 1, 1),
                publication_end=date(2026, 12, 31),
            ),
        )
        self.assertEqual(len(result), 87)

    def test_different_filter_groups_use_and(self):
        start_date = date(2025, 1, 1)
        result = filter_patents(
            self.patents,
            SearchQuery(
                patent_types=("invention",),
                ipc_prefixes=("H01L",),
                publication_start=start_date,
            ),
        )

        self.assertGreater(len(result), 0)
        self.assertTrue((result["type"] == "invention").all())
        self.assertTrue((result["_publication_date"] >= pd.Timestamp(start_date)).all())
        self.assertTrue(
            result["_ipc"].map(
                lambda codes: any(code.startswith("H01L") for code in codes)
            ).all()
        )

    def test_invalid_date_range_fails(self):
        query = SearchQuery(
            publication_start=date(2026, 2, 1),
            publication_end=date(2026, 1, 1),
        )
        with self.assertRaisesRegex(ValueError, "start date"):
            filter_patents(self.patents, query)

    def test_unprepared_dataframe_fails(self):
        with self.assertRaisesRegex(ValueError, "not prepared"):
            filter_patents(pd.DataFrame({"title": ["Example"]}), SearchQuery())


if __name__ == "__main__":
    unittest.main()

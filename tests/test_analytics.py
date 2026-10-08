"""Tests for analytics on complete and filtered patent datasets."""

import unittest
from datetime import date

from patents.analytics import applicant_ranking, ipc_distribution, yearly_trend
from patents.data import initialize_data
from patents.search import SearchQuery, filter_patents


class PatentAnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patents, _ = initialize_data()

    def test_applicant_ranking_uses_patent_counts(self):
        ranking = applicant_ranking(self.patents)

        self.assertEqual(len(ranking), 10)
        self.assertEqual(ranking.iloc[0].to_dict(), {
            "applicant": "台灣積體電路製造股份有限公司",
            "patent_count": 22,
        })

    def test_yearly_trend_uses_publication_year(self):
        trend = yearly_trend(self.patents)

        self.assertEqual(
            trend.set_index("publication_year")["patent_count"].to_dict(),
            {2022: 106, 2023: 96, 2024: 100, 2025: 96, 2026: 87},
        )
        self.assertEqual(trend["patent_count"].sum(), 485)

    def test_ipc_distribution_counts_each_patent_once_per_prefix(self):
        distribution = ipc_distribution(self.patents, top_n=None)
        h01l_count = distribution.loc[
            distribution["ipc_prefix"] == "H01L", "patent_count"
        ].iloc[0]

        self.assertEqual(h01l_count, 150)

        sample = self.patents.head(2).copy(deep=True)
        sample.at[sample.index[0], "_ipc"] = ["H01L001/00", "H01L002/00"]
        sample.at[sample.index[1], "_ipc"] = ["H01L003/00"]
        sample_distribution = ipc_distribution(sample, top_n=None)
        self.assertEqual(sample_distribution.iloc[0].to_dict(), {
            "ipc_prefix": "H01L",
            "patent_count": 2,
        })

    def test_analytics_accept_filtered_search_results(self):
        filtered = filter_patents(
            self.patents,
            SearchQuery(
                publication_start=date(2026, 1, 1),
                publication_end=date(2026, 12, 31),
            ),
        )
        trend = yearly_trend(filtered)

        self.assertEqual(len(filtered), 87)
        self.assertEqual(trend.to_dict("records"), [
            {"publication_year": 2026, "patent_count": 87}
        ])

    def test_empty_results_return_stable_schemas(self):
        empty = self.patents.iloc[0:0]

        self.assertEqual(
            applicant_ranking(empty).columns.tolist(),
            ["applicant", "patent_count"],
        )
        self.assertEqual(
            yearly_trend(empty).columns.tolist(),
            ["publication_year", "patent_count"],
        )
        self.assertEqual(
            ipc_distribution(empty).columns.tolist(),
            ["ipc_prefix", "patent_count"],
        )

    def test_invalid_top_n_fails(self):
        with self.assertRaisesRegex(ValueError, "top_n"):
            applicant_ranking(self.patents, top_n=0)
        with self.assertRaisesRegex(ValueError, "top_n"):
            ipc_distribution(self.patents, top_n=-1)


if __name__ == "__main__":
    unittest.main()

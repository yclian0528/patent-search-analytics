"""Integration tests for the Streamlit interface."""

import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from app import get_selected_patent_no


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class StreamlitAppTests(unittest.TestCase):
    def test_app_loads_all_patents_without_errors(self):
        app = AppTest.from_file(APP_PATH).run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "485")
        self.assertEqual(len(app.dataframe[0].value), 485)
        self.assertEqual(len(app.selectbox), 0)

    def test_keyword_form_updates_results_and_detail_options(self):
        app = AppTest.from_file(APP_PATH).run(timeout=20)
        app.text_input[0].set_value("LED")
        next(button for button in app.button if button.label == "搜尋").click()
        app.run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "13")
        self.assertEqual(len(app.dataframe[0].value), 13)

    def test_selected_row_maps_to_the_patent_number(self):
        table = pd.DataFrame({"公告號": ["TWI000001B", "TWI000002B"]})

        self.assertEqual(get_selected_patent_no(table, []), "TWI000001B")
        self.assertEqual(get_selected_patent_no(table, [1]), "TWI000002B")
        self.assertEqual(get_selected_patent_no(table, [99]), "TWI000001B")


if __name__ == "__main__":
    unittest.main()

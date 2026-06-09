import pandas as pd
import unittest

from common.data_tools import merge_conso_prod_data


class DataToolsTests(unittest.TestCase):
    def test_merge_conso_prod_data_adds_cost_columns_from_price_series(self):
        conso_df = pd.DataFrame(
            {
                "datetime": ["2024-01-01T00:00:00", "2024-01-01T00:30:00"],
                "consumption": [1000, 2000],
            }
        )
        prod_df = pd.DataFrame(
            {
                "datetime": ["2024-01-01T00:00:00", "2024-01-01T00:30:00"],
                "production": [500, 0],
            }
        )
        price_df = pd.DataFrame(
            {
                "datetime": ["2024-01-01T00:00:00", "2024-01-01T00:30:00"],
                "price_eur_per_kwh": [0.25, 0.30],
            }
        )

        merged_df = merge_conso_prod_data(conso_df, prod_df, price_df=price_df)

        self.assertIn("consumption_cost_eur", merged_df.columns)
        self.assertIn("production_savings_eur", merged_df.columns)
        self.assertAlmostEqual(merged_df.loc[0, "consumption_cost_eur"], 0.25)
        self.assertAlmostEqual(merged_df.loc[0, "production_savings_eur"], 0.125)


if __name__ == "__main__":
    unittest.main()

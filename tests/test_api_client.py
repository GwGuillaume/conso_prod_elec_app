import unittest

from conso_api_tools.api_client import group_interval_readings_by_day


class ApiClientTests(unittest.TestCase):
    def test_group_interval_readings_by_day_splits_data_per_day(self):
        data = {
            "interval_reading": [
                {"date": "2026-05-10T00:00:00+00:00", "value": 1.0},
                {"date": "2026-05-10T01:00:00+00:00", "value": 2.0},
                {"date": "2026-05-11T00:00:00+00:00", "value": 3.0},
            ]
        }

        grouped = group_interval_readings_by_day(data)

        self.assertEqual(list(grouped.keys()), ["2026-05-10", "2026-05-11"])
        self.assertEqual([item["value"] for item in grouped["2026-05-10"]], [1.0, 2.0])
        self.assertEqual([item["value"] for item in grouped["2026-05-11"]], [3.0])


if __name__ == "__main__":
    unittest.main()

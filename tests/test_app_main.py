import importlib
import unittest


class AppMainTests(unittest.TestCase):
    def test_app_main_imports_without_error(self):
        module = importlib.import_module("app.main")
        self.assertTrue(hasattr(module, "main"))


if __name__ == "__main__":
    unittest.main()

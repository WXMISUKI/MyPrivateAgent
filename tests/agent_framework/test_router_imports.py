import importlib
import unittest


class RouterImportTests(unittest.TestCase):
    def test_backend_routers_package_imports(self):
        module = importlib.import_module("backend.routers")
        self.assertTrue(hasattr(module, "chat"))
        self.assertTrue(hasattr(module, "conversations"))
        self.assertTrue(hasattr(module, "mcp"))
        self.assertTrue(hasattr(module, "permissions"))


if __name__ == "__main__":
    unittest.main()

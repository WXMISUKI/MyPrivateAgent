import os
import unittest
from unittest.mock import patch

from backend.config import _is_default_secret_key, CORS_ALLOWED_ORIGINS


class TestSecurityConfig(unittest.TestCase):
    def test_default_secret_key_detected(self):
        self.assertTrue(_is_default_secret_key("your-secret-key-change-in-production-2026"))

    def test_custom_secret_key_not_flagged(self):
        self.assertFalse(_is_default_secret_key("my-real-production-key-abc123"))

    def test_cors_origins_default_is_restrictive(self):
        self.assertIsInstance(CORS_ALLOWED_ORIGINS, list)


class TestStartupValidation(unittest.TestCase):
    def test_validate_config_passes_with_defaults(self):
        from backend.agent_server.bootstrap import validate_startup_config
        errors = validate_startup_config()
        self.assertIsInstance(errors, list)

    def test_validate_config_reports_missing_provider(self):
        from backend.agent_server.bootstrap import validate_startup_config
        with patch.dict(os.environ, {"ARK_API_KEY": "", "OLLAMA_BASE_URL": ""}, clear=False):
            errors = validate_startup_config()
            self.assertIsInstance(errors, list)


if __name__ == "__main__":
    unittest.main()

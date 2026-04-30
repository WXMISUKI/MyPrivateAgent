import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.services.provider_config_service import ProviderConfigService


class TestProviderConfigService(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.service = ProviderConfigService(data_dir=Path(self.tmp_dir))

    def tearDown(self):
        config_path = Path(self.tmp_dir) / "provider_config.json"
        if config_path.exists():
            config_path.unlink()
        os.rmdir(self.tmp_dir)

    def test_list_providers_returns_known_providers(self):
        providers = self.service.list_providers()
        names = [p["name"] for p in providers]
        self.assertIn("volcengine-ark", names)
        self.assertIn("ollama", names)

    def test_api_key_masked(self):
        providers = self.service.list_providers()
        for p in providers:
            if p.get("api_key_masked"):
                self.assertNotIn("ARK_API_KEY", p["api_key_masked"])

    def test_update_provider_saves_to_file(self):
        self.service.update_provider("volcengine-ark", {
            "api_key": "sk-test-key-12345678",
            "base_url": "https://custom.endpoint.com/v3",
        })
        config_path = Path(self.tmp_dir) / "provider_config.json"
        self.assertTrue(config_path.exists())
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(data["volcengine-ark"]["api_key"], "sk-test-key-12345678")
        self.assertEqual(data["volcengine-ark"]["base_url"], "https://custom.endpoint.com/v3")

    def test_get_effective_config_prefers_local_override(self):
        self.service.update_provider("volcengine-ark", {
            "api_key": "sk-override-key",
        })
        config = self.service.get_effective_config("volcengine-ark")
        self.assertEqual(config["api_key"], "sk-override-key")
        self.assertEqual(config["config_source"], "local_override")

    def test_get_effective_config_falls_back_to_env(self):
        config = self.service.get_effective_config("volcengine-ark")
        self.assertIn(config["config_source"], ("env", "unconfigured"))

    def test_mask_api_key(self):
        self.assertEqual(self.service.mask_api_key("sk-abcdefghijklmnop"), "sk-a****mnop")
        self.assertEqual(self.service.mask_api_key("short"), "****")
        self.assertIsNone(self.service.mask_api_key(None))
        self.assertIsNone(self.service.mask_api_key(""))

    def test_update_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            self.service.update_provider("unknown-provider", {"api_key": "test"})

    def test_update_provider_saves_model_name(self):
        self.service.update_provider("volcengine-ark", {
            "model_name": "doubao-pro-32k",
        })
        config = self.service.get_effective_config("volcengine-ark")
        self.assertEqual(config["model_name"], "doubao-pro-32k")
        self.assertEqual(config["config_source"], "local_override")

    def test_list_providers_includes_model_name(self):
        providers = self.service.list_providers()
        for p in providers:
            self.assertIn("model_name", p)


if __name__ == "__main__":
    unittest.main()

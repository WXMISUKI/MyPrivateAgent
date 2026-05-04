import unittest
import uuid
import shutil
from pathlib import Path

from backend.services.runtime_surface_config_service import RuntimeSurfaceConfigService


class RuntimeSurfaceConfigServiceTests(unittest.TestCase):
    def setUp(self):
        base_dir = Path("tests/agent_framework/.tmp_runtime_surface_config")
        base_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir = base_dir / f"case_{uuid.uuid4().hex}"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.tmp_dir / "runtime_surface.json"
        self.service = RuntimeSurfaceConfigService(config_path=self.config_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_defaults_include_failover_thresholds(self):
        defaults = self.service.get_defaults()
        self.assertIn("failover_thresholds", defaults)
        self.assertEqual(defaults["failover_thresholds"]["medium"], 0.2)
        self.assertEqual(defaults["failover_thresholds"]["high"], 0.4)

    def test_update_overrides_accepts_failover_thresholds(self):
        updated = self.service.update_overrides({
            "failover_thresholds": {
                "medium": 0.25,
                "high": 0.55,
            }
        })
        self.assertEqual(updated["failover_thresholds"]["medium"], 0.25)
        self.assertEqual(updated["failover_thresholds"]["high"], 0.55)

    def test_update_overrides_rejects_invalid_failover_thresholds(self):
        with self.assertRaises(ValueError):
            self.service.update_overrides({"failover_thresholds": "invalid"})
        with self.assertRaises(ValueError):
            self.service.update_overrides({"failover_thresholds": {"medium": -1, "high": 0.5}})
        with self.assertRaises(ValueError):
            self.service.update_overrides({"failover_thresholds": {"medium": 0.5, "high": 0.5}})


if __name__ == "__main__":
    unittest.main()

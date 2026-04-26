import time
import unittest

from backend.agent_framework.tool_cache import ToolResultCache


class ToolResultCacheTests(unittest.TestCase):
    def test_cache_key_normalizes_argument_order(self):
        cache = ToolResultCache()
        cache.set("search", {"b": 2, "a": 1}, "ok", ttl_seconds=10)

        result = cache.get("search", {"a": 1, "b": 2})
        self.assertEqual(result, "ok")

    def test_cache_expiry_removes_stale_entry(self):
        cache = ToolResultCache()
        cache.set("search", {"query": "舟山天气"}, "cached", ttl_seconds=0.01)

        time.sleep(0.03)
        self.assertIsNone(cache.get("search", {"query": "舟山天气"}))

    def test_clear_removes_all_entries(self):
        cache = ToolResultCache()
        cache.set("search", {"query": "舟山天气"}, "cached", ttl_seconds=10)
        cache.clear()

        self.assertIsNone(cache.get("search", {"query": "舟山天气"}))


if __name__ == "__main__":
    unittest.main()

import unittest

from backend.agent_framework.tool_cache import get_tool_result_cache
from backend.agent_framework.tools import ToolSpec
from backend.harness.agent_harness import AgentHarness
from backend.harness.tool_registry import get_registry


class _CachedTool:
    def __init__(self):
        self.call_count = 0

    async def ainvoke(self, args):
        self.call_count += 1
        return f"result:{args['query']}"


class AgentHarnessCacheTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.registry = get_registry()
        self.cache = get_tool_result_cache()
        self.cache.clear()

    async def asyncTearDown(self):
        self.cache.clear()

    async def test_execute_tool_uses_runtime_cache_for_cacheable_tool(self):
        tool_name = "cached_test_tool"
        self.registry.register_tool_spec(
            ToolSpec(
                name=tool_name,
                description="test cache tool",
                supports_cache=True,
                cache_ttl_seconds=300,
            )
        )

        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)
        stub_tool = _CachedTool()
        harness.tool_map[tool_name] = stub_tool

        first, first_metadata = await harness._execute_tool_with_metadata(tool_name, {"query": "舟山天气"})
        second, second_metadata = await harness._execute_tool_with_metadata(tool_name, {"query": "舟山天气"})

        self.assertEqual(first, "result:舟山天气")
        self.assertEqual(second, "result:舟山天气")
        self.assertEqual(stub_tool.call_count, 1)
        self.assertFalse(first_metadata["cache_hit"])
        self.assertEqual(first_metadata["result_source"], "tool")
        self.assertTrue(second_metadata["cache_hit"])
        self.assertEqual(second_metadata["result_source"], "runtime_cache")


if __name__ == "__main__":
    unittest.main()

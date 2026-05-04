import unittest

from backend.services.command_registry_service import get_command_registry_service


class CommandRegistryServiceTests(unittest.TestCase):
    def test_runtime_contract_includes_framework_commands(self):
        service = get_command_registry_service()
        contract = service.build_runtime_contract()

        self.assertGreaterEqual(contract["total_commands"], 10)
        doctor_command = next(cmd for cmd in contract["framework_commands"] if cmd["name"] == "doctor")
        self.assertTrue(doctor_command["has_param"])
        self.assertEqual(doctor_command["param_hint"], "/doctor <startup|governance> [warning]")
        self.assertIn("governance", doctor_command["param_examples"])
        self.assertIn("governance warning", doctor_command["param_examples"])
        snapshot_command = next(cmd for cmd in contract["framework_commands"] if cmd["name"] == "snapshot")
        self.assertTrue(snapshot_command["has_param"])
        self.assertEqual(snapshot_command["param_hint"], "/snapshot <snapshot_id>")
        self.assertIn("MCP-REF-1", snapshot_command["param_examples"])
        gaps_command = next(cmd for cmd in contract["framework_commands"] if cmd["name"] == "gaps")
        self.assertTrue(gaps_command["has_param"])
        self.assertEqual(gaps_command["param_hint"], "/gaps <all|warning|snapshot <id>>")
        self.assertIn("warning", gaps_command["param_examples"])
        self.assertIn("snapshot GOV-REF-1", gaps_command["param_examples"])
        self.assertTrue(any(cmd["name"] == "plan" for cmd in contract["framework_commands"]))
        self.assertTrue(any(cmd["name"] == "memory" for cmd in contract["framework_commands"]))


if __name__ == "__main__":
    unittest.main()

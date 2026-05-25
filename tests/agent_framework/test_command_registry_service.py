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

    def test_runtime_contract_exposes_command_definitions_and_sdk_interface(self):
        service = get_command_registry_service()
        contract = service.build_runtime_contract()

        self.assertEqual(contract["contract_version"], "phase-b-command-runtime-v1")
        definitions = {item["name"]: item for item in contract["command_definitions"]}
        doctor = definitions["doctor"]
        self.assertEqual(doctor["command_id"], "doctor")
        self.assertEqual(doctor["permission_level"], "read")
        self.assertEqual(doctor["execution_handler"], "command_handlers.run_doctor")
        self.assertIn("mode", doctor["parameters_schema"]["properties"])
        self.assertIn("governance.runtime_read", doctor["required_capabilities"])

        sdk = contract["embedded_sdk"]
        self.assertEqual(sdk["contract_version"], "phase-b-embedded-sdk-v1")
        self.assertEqual(
            [item["method"] for item in sdk["methods"]],
            [
                "create_run",
                "stream_events",
                "list_continuation_bindings",
                "probe_run_recovery",
                "register_tool",
                "submit_approval",
                "resume_run",
                "delegate_run",
                "evaluate_child_executor_preflight",
                "evaluate_child_executor_gate",
                "evaluate_child_executor_routing",
                "bind_child_executor_routing",
                "execute_bound_child_executor_stub",
                "execute_bound_child_executor",
                "merge_child_executor_output",
                "list_child_executor_outputs",
                "summarize_child_executor_outputs",
                "summarize_child_executor_merged_semantics",
                "create_artifact",
                "list_artifacts",
                "execute_run",
            ],
        )
        stability_by_method = {item["method"]: item["stability"] for item in sdk["methods"]}
        self.assertEqual(stability_by_method["create_run"], "preview")
        self.assertEqual(stability_by_method["stream_events"], "preview")
        self.assertEqual(stability_by_method["list_continuation_bindings"], "preview")
        self.assertEqual(stability_by_method["probe_run_recovery"], "preview")
        self.assertEqual(stability_by_method["submit_approval"], "preview")
        self.assertEqual(stability_by_method["resume_run"], "preview")
        self.assertEqual(stability_by_method["delegate_run"], "preview")
        self.assertEqual(stability_by_method["evaluate_child_executor_preflight"], "preview")
        self.assertEqual(stability_by_method["evaluate_child_executor_gate"], "preview")
        self.assertEqual(stability_by_method["evaluate_child_executor_routing"], "preview")
        self.assertEqual(stability_by_method["bind_child_executor_routing"], "preview")
        self.assertEqual(stability_by_method["execute_bound_child_executor_stub"], "preview")
        self.assertEqual(stability_by_method["execute_bound_child_executor"], "preview")
        self.assertEqual(stability_by_method["merge_child_executor_output"], "preview")
        self.assertEqual(stability_by_method["list_child_executor_outputs"], "preview")
        self.assertEqual(stability_by_method["summarize_child_executor_outputs"], "preview")
        self.assertEqual(stability_by_method["summarize_child_executor_merged_semantics"], "preview")
        self.assertEqual(stability_by_method["create_artifact"], "preview")
        self.assertEqual(stability_by_method["list_artifacts"], "preview")
        self.assertEqual(stability_by_method["execute_run"], "preview")
        self.assertEqual(stability_by_method["register_tool"], "draft")
        event_status_kinds = {item["status_kind"]: item for item in sdk["event_status_kinds"]}
        self.assertEqual(event_status_kinds["loop_continuation_registered"]["stability"], "preview")
        self.assertEqual(event_status_kinds["loop_continuation_consumed"]["category"], "continuation")
        self.assertEqual(event_status_kinds["loop_continuation_discarded"]["required_payload"], ["loop_continuation"])
        self.assertEqual(event_status_kinds["execution_loop_done"]["event_type"], "done")
        self.assertIn("run_workspace_snapshot", sdk["persistence_seams"])
        self.assertIn("_tool_continuations", sdk["volatile_runtime_state"])
        self.assertEqual(sdk["delegate_preflight"]["status"], "relationship_only")

        facade = contract["agent_harness_facade"]
        self.assertEqual(facade["contract_version"], "phase-e-agent-harness-facade-v1")
        self.assertEqual(facade["runtime_backend"], "EmbeddedAgentRuntimeSDK")
        self.assertEqual(
            [item["method"] for item in facade["methods"]],
            ["run", "stream", "list_continuation_bindings", "probe_recovery", "approve", "resume", "delegate", "evaluate_delegate_preflight", "evaluate_delegate_gate", "evaluate_delegate_routing", "bind_delegate_routing", "execute_delegate_stub", "execute_delegate", "merge_delegate_output", "list_delegate_outputs", "summarize_delegate_outputs", "create_artifact", "list_artifacts", "register_tool", "execute"],
        )
        facade_stability_by_method = {item["method"]: item["stability"] for item in facade["methods"]}
        self.assertEqual(facade_stability_by_method["list_continuation_bindings"], "preview")
        self.assertEqual(facade_stability_by_method["probe_recovery"], "preview")
        self.assertEqual(facade_stability_by_method["register_tool"], "preview")
        self.assertEqual(facade["delegate_preflight"]["status"], "relationship_only")
        self.assertEqual(facade["facade_runtime_posture"], "embedded_harness_v1_candidate")
        self.assertTrue(facade["tool_registry_bridge"]["local_tool_spec_registry"])
        self.assertEqual(facade["default_tool_executor"]["trace_model"], "sdk_tool_events")

        runtime_factory = contract["embedded_runtime_factory"]
        self.assertEqual(runtime_factory["contract_version"], "phase-ii-embedded-runtime-factory-v1")
        self.assertTrue(runtime_factory["shared_default_runtime"])
        self.assertEqual(runtime_factory["runtime_backend"], "EmbeddedAgentRuntimeSDK")
        self.assertIn("workspace_store", runtime_factory["dependency_sources"])
        self.assertIn("continuation_registry", runtime_factory["dependency_sources"])
        self.assertIn("db_mode", runtime_factory["default_runtime_profile"])
        self.assertIn("db_mode_source", runtime_factory["default_runtime_profile"])
        self.assertIn("embedded_workspace_store_mode", runtime_factory["default_runtime_profile"])
        self.assertIn("embedded_workspace_store_mode_source", runtime_factory["default_runtime_profile"])
        self.assertIn("default_runtime_mode", runtime_factory["default_runtime_profile"])
        self.assertIn("recovery_posture", runtime_factory["default_runtime_profile"])
        self.assertIn("workspace_strategy_rule", runtime_factory["default_runtime_profile"])
        self.assertIn("durable_by_default", runtime_factory["default_runtime_profile"])
        self.assertIn("recommended_bootstrap", runtime_factory["default_runtime_profile"])
        self.assertIn("configurable_bootstrap_knobs", runtime_factory["default_runtime_profile"])
        self.assertIn("hot_reloadable_bootstrap_knobs", runtime_factory["default_runtime_profile"])
        self.assertIn("restart_required_bootstrap_knobs", runtime_factory["default_runtime_profile"])
        self.assertIn("runtime.run_recovery_probe", runtime_factory["recovery_capabilities"])
        self.assertEqual(runtime_factory["factory_methods"], ["create_sdk", "create_agent"])


if __name__ == "__main__":
    unittest.main()

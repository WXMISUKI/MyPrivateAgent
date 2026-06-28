import unittest
from unittest.mock import patch

from backend.routers import providers as providers_router
from backend.services.provider_ops_service import ProviderOpsService


class _FakeProviderConfigService:
    def __init__(self, providers):
        self._providers = providers

    def list_providers(self):
        return list(self._providers)


class ProviderOpsServiceTests(unittest.TestCase):
    def test_list_provider_ops_reports_compact_posture(self):
        service = ProviderOpsService(
            provider_config_service=_FakeProviderConfigService(
                [
                    {
                        "name": "volcengine-ark",
                        "display_name": "火山引擎 Ark (豆包)",
                        "requires_api_key": True,
                        "configured": True,
                        "api_key_masked": "sk-a****mnop",
                        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                        "model_name": "doubao-seed-2-0-mini-260215",
                        "config_source": "local_override",
                    }
                ]
            )
        )

        contract = service.list_provider_ops()

        self.assertEqual(contract["contract_version"], "provider-ops-control-plane-v1")
        self.assertEqual(contract["summary"]["total"], 1)
        self.assertEqual(contract["providers"][0]["provider_id"], "volcengine-ark")
        self.assertEqual(contract["providers"][0]["credential_posture"], "configured")
        self.assertEqual(contract["providers"][0]["quota_posture"], "unknown")
        self.assertEqual(contract["providers"][0]["fallback_posture"], "ready")
        self.assertNotIn("api_key", contract["providers"][0])

    def test_list_provider_ops_marks_unconfigured_provider_closed(self):
        service = ProviderOpsService(
            provider_config_service=_FakeProviderConfigService(
                [
                    {
                        "name": "ollama",
                        "display_name": "Ollama (本地)",
                        "requires_api_key": False,
                        "configured": False,
                        "api_key_masked": None,
                        "base_url": "http://localhost:11434",
                        "model_name": "",
                        "config_source": "unconfigured",
                    }
                ]
            )
        )

        contract = service.list_provider_ops()

        provider = contract["providers"][0]
        self.assertEqual(provider["overall_status"], "unconfigured")
        self.assertEqual(provider["next_action"], "configure_provider_credentials_before_use")
        self.assertEqual(provider["fallback_posture"], "blocked")

    @patch("backend.routers.providers.get_provider_ops_service")
    def test_provider_ops_route_delegates_to_service(self, mock_get_service):
        mock_get_service.return_value = ProviderOpsService(
            provider_config_service=_FakeProviderConfigService([])
        )

        contract = providers_router.list_provider_ops()

        self.assertEqual(contract["contract_version"], "provider-ops-control-plane-v1")
        self.assertEqual(contract["summary"]["total"], 0)


if __name__ == "__main__":
    unittest.main()

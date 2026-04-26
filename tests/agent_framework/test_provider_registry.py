import unittest

from backend.agent_framework.providers import ModelProviderRegistry


class FakeProvider:
    def __init__(self, name, supported_prefix, reasoning=False):
        self.provider_name = name
        self.supported_prefix = supported_prefix
        self.reasoning = reasoning

    def supports_model(self, model_name: str) -> bool:
        return model_name.startswith(self.supported_prefix)

    def get_model(self, model_name: str, purpose: str = "main"):
        return {"provider": self.provider_name, "model": model_name, "purpose": purpose}

    def get_model_config(self, model_name: str):
        return {
            "name": model_name,
            "provider": self.provider_name,
            "supports_reasoning": self.reasoning,
        }

    def is_model_available(self, model_name: str) -> bool:
        return True

    def list_available_models(self):
        return {
            f"{self.supported_prefix}-demo": {
                "name": f"{self.supported_prefix}-demo",
                "provider": self.provider_name,
                "available": True,
            }
        }


class ProviderRegistryTests(unittest.TestCase):
    def test_registry_resolves_matching_provider(self):
        registry = ModelProviderRegistry()
        registry.register_backend(FakeProvider("cloud", "doubao", reasoning=False))
        registry.register_backend(FakeProvider("local", "llama", reasoning=False))

        model = registry.get_model("doubao", purpose="main")
        self.assertEqual(model["provider"], "cloud")

        config = registry.get_model_config("llama3.1")
        self.assertEqual(config["provider"], "local")

    def test_registry_merges_available_models(self):
        registry = ModelProviderRegistry()
        registry.register_backend(FakeProvider("cloud", "doubao", reasoning=False))
        registry.register_backend(FakeProvider("local", "llama", reasoning=False))

        models = registry.list_available_models()
        self.assertIn("doubao-demo", models)
        self.assertIn("llama-demo", models)

    def test_registry_raises_for_unknown_model(self):
        registry = ModelProviderRegistry()
        registry.register_backend(FakeProvider("cloud", "doubao", reasoning=False))

        with self.assertRaises(ValueError):
            registry.get_model("unknown-model")


if __name__ == "__main__":
    unittest.main()

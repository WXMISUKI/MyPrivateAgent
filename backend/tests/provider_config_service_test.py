from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.services.provider_config_service import CONFIG_FILENAME, ProviderConfigService


def test_list_providers_masks_api_key_and_uses_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARK_API_KEY", "abcd1234wxyz5678")
    monkeypatch.setenv("ARK_BASE_URL", "http://ark.local")
    monkeypatch.setenv("ARK_MODEL", "doubao-test")

    service = ProviderConfigService(data_dir=tmp_path)
    providers = service.list_providers()

    ark = next(item for item in providers if item["name"] == "volcengine-ark")

    assert ark["configured"] is True
    assert ark["config_source"] == "env"
    assert ark["base_url"] == "http://ark.local"
    assert ark["model_name"] == "doubao-test"
    assert ark["api_key_masked"] == "abcd****5678"


def test_update_provider_persists_local_override(tmp_path: Path) -> None:
    service = ProviderConfigService(data_dir=tmp_path)

    result = service.update_provider(
        "ollama",
        {
            "base_url": "http://127.0.0.1:11435",
            "model_name": "llama3.1",
        },
    )

    assert result["status"] == "saved"
    assert result["config_source"] == "local_override"

    config_path = tmp_path / CONFIG_FILENAME
    assert config_path.exists()

    saved = json.loads(config_path.read_text(encoding="utf-8"))
    assert saved["ollama"]["base_url"] == "http://127.0.0.1:11435"
    assert saved["ollama"]["model_name"] == "llama3.1"

    effective = service.get_effective_config("ollama")
    assert effective["base_url"] == "http://127.0.0.1:11435"
    assert effective["model_name"] == "llama3.1"


def test_unknown_provider_update_fails_closed(tmp_path: Path) -> None:
    service = ProviderConfigService(data_dir=tmp_path)

    with pytest.raises(ValueError, match="Unknown provider"):
        service.update_provider("not-a-provider", {"base_url": "http://example"})

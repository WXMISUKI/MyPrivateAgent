import unittest

from backend.voice_runtime.service import VoiceRuntimeSettings, VoiceRuntimeService


class VoiceRuntimeServiceTests(unittest.TestCase):
    def test_capabilities_are_disabled_by_default_without_optional_dependencies(self):
        service = VoiceRuntimeService(
            VoiceRuntimeSettings(
                enabled=False,
                asr_provider="vosk_server",
                tts_provider="edge_tts",
                vosk_server_url="ws://127.0.0.1:2700",
            )
        )

        capabilities = service.get_capabilities()

        self.assertFalse(capabilities["enabled"])
        self.assertEqual(capabilities["contract_version"], "voice-runtime-v1")
        self.assertEqual(capabilities["asr"]["provider"], "vosk_server")
        self.assertEqual(capabilities["asr"]["status"], "disabled")
        self.assertTrue(capabilities["asr"]["realtime_supported"])
        self.assertEqual(capabilities["tts"]["provider"], "edge_tts")
        self.assertEqual(capabilities["tts"]["status"], "disabled")

    def test_enabled_runtime_reports_provider_dependency_status_without_import_time_failure(self):
        service = VoiceRuntimeService(
            VoiceRuntimeSettings(
                enabled=True,
                asr_provider="vosk_server",
                tts_provider="edge_tts",
                vosk_server_url="",
            )
        )

        capabilities = service.get_capabilities()

        self.assertTrue(capabilities["enabled"])
        self.assertEqual(capabilities["asr"]["status"], "unconfigured")
        self.assertIn("VOSK_SERVER_URL", capabilities["asr"]["reason"])
        self.assertIn(capabilities["tts"]["status"], {"ready", "missing_dependency"})

    def test_tts_returns_structured_unavailable_result_when_runtime_disabled(self):
        service = VoiceRuntimeService(
            VoiceRuntimeSettings(enabled=False, tts_provider="edge_tts")
        )

        result = service.synthesize_speech({"text": "你好"})

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "VOICE_RUNTIME_DISABLED")

    def test_asr_returns_structured_unavailable_result_when_runtime_disabled(self):
        service = VoiceRuntimeService(
            VoiceRuntimeSettings(enabled=False, asr_provider="vosk_server")
        )

        result = service.transcribe_audio(b"test", media_type="audio/pcm")

        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"]["code"], "VOICE_RUNTIME_DISABLED")


if __name__ == "__main__":
    unittest.main()

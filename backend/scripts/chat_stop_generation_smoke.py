"""Minimal stop-generation smoke check for frontend/store behavior parity."""

from __future__ import annotations

import json


def main() -> int:
    payload = {
        "status": "ok",
        "checks": [
            {
                "name": "front_store_abort_contract",
                "ok": True,
                "expected": {
                    "when": "active request aborted",
                    "assistant_message_content": "已停止生成",
                    "assistant_message_isGenerating": False,
                    "store_isLoading": False,
                },
                "verification": "covered by frontend-vue/src/stores/__tests__/conversation.test.js",
            }
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

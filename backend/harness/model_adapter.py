# -*- coding: utf-8 -*-
import json
import re
import logging
from typing import AsyncGenerator, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ModelAdapter:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.last_content = ""

    def is_reasoning_model(self) -> bool:
        model_lower = self.model_name.lower()
        return "deepseek" in model_lower and "r1" in model_lower

    async def process_stream(self, chunks: AsyncGenerator, skip_reasoning: bool = False):
        self.last_content = ""
        async for chunk in chunks:
            parsed = self._parse_chunk(chunk)
            if parsed is None:
                continue
            if parsed['type'] == 'reasoning':
                if not skip_reasoning:
                    yield parsed
            elif parsed['type'] == 'content':
                new_content = self._deduplicate(parsed['content'])
                if new_content:
                    yield {"type": "content", "content": new_content}
            elif parsed['type'] == 'error':
                yield parsed

    def _parse_chunk(self, chunk) -> Optional[Dict[str, Any]]:
        if isinstance(chunk, str):
            try:
                data = json.loads(chunk)
                return data
            except json.JSONDecodeError:
                return {"type": "content", "content": chunk}

        if isinstance(chunk, dict):
            if chunk.get('type') == 'reasoning':
                return {"type": "reasoning", "content": chunk.get('content', '')}
            elif chunk.get('type') == 'content':
                return {"type": "content", "content": chunk.get('content', '')}
            elif chunk.get('error'):
                return {"type": "error", "content": chunk.get('error')}

        if hasattr(chunk, 'content'):
            content = chunk.content
            reasoning = self._extract_reasoning(chunk)
            if reasoning:
                return {"type": "reasoning", "content": reasoning, "raw_content": content}
            return {"type": "content", "content": content}

        return None

    def _extract_reasoning(self, chunk) -> str:
        reasoning = ""
        if hasattr(chunk, 'response_metadata') and chunk.response_metadata:
            metadata = chunk.response_metadata
            reasoning = metadata.get('reasoning_content', '') or metadata.get('reasoning', '')

        if not reasoning and hasattr(chunk, 'raw') and chunk.raw:
            try:
                raw = chunk.raw
                if isinstance(raw, dict):
                    choices = raw.get('choices', [{}])[0] if raw.get('choices') else {}
                    delta = choices.get('delta', {})
                    reasoning = delta.get('reasoning_content', '')
            except Exception:
                pass

        return reasoning

    def _deduplicate(self, content: str) -> str:
        if not content:
            return ""
        if self.last_content and content.startswith(self.last_content):
            new_content = content[len(self.last_content):]
            self.last_content = content
            return new_content
        if not self.last_content:
            self.last_content = content
            return content
        self.last_content = content
        return content


class OllamaAdapter(ModelAdapter):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        self.full_content = ""

    def _parse_chunk(self, chunk) -> Optional[Dict[str, Any]]:
        if hasattr(chunk, 'content'):
            content = chunk.content
            if self.is_reasoning_model():
                reasoning = self._extract_reasoning_from_content(content)
                if reasoning:
                    return {"type": "reasoning", "content": reasoning}
                if content.startswith('\n\n') or content.startswith('好的') or content.startswith('我是'):
                    return {"type": "content", "content": content}
            return {"type": "content", "content": content}

        if isinstance(chunk, dict):
            if chunk.get('type') == 'reasoning':
                return {"type": "reasoning", "content": chunk.get('content', '')}
            elif chunk.get('type') == 'content':
                return {"type": "content", "content": chunk.get('content', '')}

        if isinstance(chunk, str):
            try:
                return json.loads(chunk)
            except json.JSONDecodeError:
                return {"type": "content", "content": chunk}

        return None

    def _extract_reasoning_from_content(self, content: str) -> str:
        if '----' in content or '--' in content:
            parts = re.split(r'-{10,}', content)
            if len(parts) > 1:
                reasoning = parts[0].strip()
                if reasoning:
                    return reasoning
        return ""


def create_adapter(model_name: str) -> ModelAdapter:
    model_lower = model_name.lower()
    if "ollama" in model_lower or "llama" in model_lower or "deepseek" in model_lower:
        return OllamaAdapter(model_name)
    return ModelAdapter(model_name)

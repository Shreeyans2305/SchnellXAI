from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from ..config import settings


class OllamaClient:
    """
    Thin async client for interacting with a local Ollama instance.

    Uses the /api/chat endpoint and expects the Gemma model to be available.
    """

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = base_url or settings.ollama_host
        self.model = model or settings.ollama_model
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def chat(self, system: str, messages: List[Dict[str, str]]) -> str:
        """
        Send a chat completion request and return the model's text content.

        On any error, returns a best-effort fallback explanation to keep the
        system running even if Ollama is unavailable.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "stream": False,
        }

        try:
            client = await self._get_client()
            resp = await client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Ollama chat API returns a single message in `message`
            message = data.get("message") or {}
            content = message.get("content")
            if isinstance(content, str):
                return content
            return json.dumps(content)
        except Exception as exc:  # noqa: BLE001
            # Fallback: degrade gracefully while surfacing the issue to the caller.
            return (
                "Ollama/Gemma backend is not reachable or returned an error. "
                f"Reason: {exc!r}. Using heuristic behavior instead."
            )

    async def chat_json(self, system: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Convenience helper for agents that expect JSON responses.

        Attempts to parse the model output as JSON; if parsing fails, returns
        an empty dict, allowing callers to fall back to deterministic logic.
        """
        content = await self.chat(system, messages)
        try:
            return json.loads(content)
        except Exception:  # noqa: BLE001
            return {}


_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


from typing import Iterator
import ollama
from .base import LLMClient


class OllamaClient(LLMClient):
    def __init__(self, host: str, model: str):
        self._client = ollama.Client(host=host)
        self.model = model

    def list_models(self) -> list[str]:
        try:
            resp = self._client.list()
            return [m.model for m in resp.models]
        except Exception:
            return []

    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        # qwen3 계열은 thinking 모드 기본값 — /no_think 로 비활성화해 즉시 응답
        msgs = list(messages)
        if "qwen3" in self.model.lower() or "qwen" in self.model.lower():
            for i in range(len(msgs) - 1, -1, -1):
                if msgs[i]["role"] == "user":
                    msgs[i] = {**msgs[i], "content": "/no_think\n" + msgs[i]["content"]}
                    break

        stream = self._client.chat(model=self.model, messages=msgs, stream=True)
        for chunk in stream:
            token = chunk.message.content
            if token:
                yield token

from typing import Iterator
from openai import OpenAI
from .base import LLMClient

OPENAI_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
GEMINI_MODELS = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class CloudClient(LLMClient):
    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self._model_list = GEMINI_MODELS if base_url else OPENAI_MODELS

    def list_models(self) -> list[str]:
        return self._model_list

    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token

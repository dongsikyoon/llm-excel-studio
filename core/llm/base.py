from abc import ABC, abstractmethod
from typing import Iterator


class LLMClient(ABC):
    @abstractmethod
    def list_models(self) -> list[str]: ...

    @abstractmethod
    def chat_stream(self, messages: list[dict]) -> Iterator[str]: ...

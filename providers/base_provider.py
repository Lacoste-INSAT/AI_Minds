from abc import ABC, abstractmethod
from typing import AsyncIterator


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict]) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, messages: list[dict]) -> AsyncIterator[str]:
        raise NotImplementedError

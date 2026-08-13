from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LLMResponse:
    text: str
    raw_response: str | dict[str, Any] | None
    model_name: str
    provider_name: str


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 1000) -> LLMResponse: ...

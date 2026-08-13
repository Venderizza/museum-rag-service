from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> list[float]: ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def get_model_name(self) -> str: ...

    @abstractmethod
    def get_dimension(self) -> int: ...

    @abstractmethod
    def get_version(self) -> str: ...

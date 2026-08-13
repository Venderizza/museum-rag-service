import hashlib
import math
from app.domain.ports.embedding_provider import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 384, model_name: str = 'mock-embedding', version: str = 'v1'):
        self.dimension = dimension
        self.model_name = model_name
        self.version = version

    async def embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode('utf-8')).digest()
        values = []
        for i in range(self.dimension):
            byte = digest[i % len(digest)]
            values.append((byte / 255.0) - 0.5)
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_text(text) for text in texts]

    def get_model_name(self) -> str:
        return self.model_name

    def get_dimension(self) -> int:
        return self.dimension

    def get_version(self) -> str:
        return self.version

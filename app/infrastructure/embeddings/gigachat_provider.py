from __future__ import annotations

import httpx

from app.domain.errors import EmbeddingProviderError
from app.domain.ports.embedding_provider import EmbeddingProvider
from app.infrastructure.gigachat.auth import GigaChatAuthClient


class GigaChatEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_url: str,
        auth_client: GigaChatAuthClient,
        model: str,
        dimension: int,
        version: str,
        verify_ssl: bool = True,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if dimension <= 0:
            raise EmbeddingProviderError('Embedding dimension must be configured explicitly for GigaChat')
        self.api_url = api_url.rstrip('/')
        self.auth_client = auth_client
        self.model = model
        self.dimension = dimension
        self.version = version
        self.verify_ssl = verify_ssl
        self.http_client = http_client

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_batch([text])
        return vectors[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        token = await self.auth_client.get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        payload = {'model': self.model, 'input': texts}

        try:
            if self.http_client is not None:
                response = await self.http_client.post(f'{self.api_url}/embeddings', headers=headers, json=payload)
            else:
                async with httpx.AsyncClient(timeout=60, verify=self.verify_ssl) as client:
                    response = await client.post(f'{self.api_url}/embeddings', headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            items = sorted(data.get('data', []), key=lambda item: item.get('index', 0))
            vectors = [item['embedding'] for item in items]
        except Exception as exc:
            raise EmbeddingProviderError(f'GigaChat embeddings request failed: {exc}') from exc

        if len(vectors) != len(texts):
            raise EmbeddingProviderError('GigaChat embeddings response size does not match request size')

        for vector in vectors:
            if len(vector) != self.dimension:
                raise EmbeddingProviderError(
                    f'GigaChat embedding dimension mismatch: expected {self.dimension}, got {len(vector)}'
                )

        return vectors

    def get_model_name(self) -> str:
        return self.model

    def get_dimension(self) -> int:
        return self.dimension

    def get_version(self) -> str:
        return self.version

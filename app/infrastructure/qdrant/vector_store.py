from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)
from app.domain.entities.chunk import Chunk
from app.domain.entities.source import Source
from app.domain.errors import VectorStoreError
from app.domain.ports.vector_store import VectorStore


class QdrantVectorStore(VectorStore):
    def __init__(self, host: str, port: int, collection_name: str):
        self.client = AsyncQdrantClient(host=host, port=port)
        self.collection_name = collection_name

    async def ensure_collection(self, vector_size: int) -> None:
        try:
            collections = await self.client.get_collections()
            existing = {collection.name for collection in collections.collections}
            if self.collection_name not in existing:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
        except Exception as exc:
            raise VectorStoreError(str(exc)) from exc

    async def upsert_chunks(
        self, chunks: list[Chunk], vectors: list[list[float]], titles: dict[int, str]
    ) -> None:
        if len(chunks) != len(vectors):
            raise VectorStoreError("chunks and vectors length mismatch")
        points = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            points.append(
                PointStruct(
                    id=str(chunk.id),
                    vector=vector,
                    payload={
                        "document_id": chunk.document_id,
                        "chunk_id": str(chunk.id),
                        "chunk_index": chunk.chunk_index,
                        "title": titles.get(chunk.document_id, ""),
                        "text": chunk.text,
                        "is_deleted": chunk.is_deleted,
                        "embedding_model_name": chunk.embedding_model_name,
                        "embedding_version": chunk.embedding_version,
                    },
                )
            )
        try:
            await self.client.upsert(collection_name=self.collection_name, points=points)
        except Exception as exc:
            raise VectorStoreError(str(exc)) from exc

    async def search(
        self, vector: list[float], top_k: int, filters: dict | None = None
    ) -> list[Source]:
        qdrant_filter = Filter(
            must=[FieldCondition(key="is_deleted", match=MatchValue(value=False))]
        )
        try:
            # qdrant-client 1.13+ uses query_points instead of AsyncQdrantClient.search.
            # Keep a fallback for older 1.x clients to make the adapter version-tolerant.
            if hasattr(self.client, "search"):
                points = await self.client.search(
                    collection_name=self.collection_name,
                    query_vector=vector,
                    query_filter=qdrant_filter,
                    limit=top_k,
                    score_threshold=0.81,
                    with_payload=True,
                )
            else:
                response = await self.client.query_points(
                    collection_name=self.collection_name,
                    query=vector,
                    query_filter=qdrant_filter,
                    score_threshold=0.81,
                    limit=top_k,
                    with_payload=True,
                )
                points = response.points

            return [
                Source(
                    document_id=int(item.payload.get("document_id")),
                    title=str(item.payload.get("title", "")),
                    score=float(item.score),
                    text=str(item.payload.get("text", "")),
                )
                for item in points
                if item.payload is not None
            ]
        except Exception as exc:
            raise VectorStoreError(str(exc)) from exc

    async def mark_deleted_by_document_id(self, document_id: int) -> None:
        qdrant_filter = Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        )
        try:
            await self.client.set_payload(
                collection_name=self.collection_name,
                payload={"is_deleted": True},
                points=FilterSelector(filter=qdrant_filter),
            )
        except TypeError:
            # Compatibility fallback for older qdrant-client versions.
            try:
                await self.client.set_payload(
                    collection_name=self.collection_name,
                    payload={"is_deleted": True},
                    points=qdrant_filter,
                )
            except Exception as exc:
                raise VectorStoreError(str(exc)) from exc
        except Exception as exc:
            raise VectorStoreError(str(exc)) from exc

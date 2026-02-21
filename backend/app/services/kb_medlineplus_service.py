"""MedlinePlus knowledge base: Actian Vector collection + semantic search."""

from __future__ import annotations

from app.core.config import settings
from app.services.memory.embedding_service import EmbeddingService

try:
    from cortex import AsyncCortexClient, DistanceMetric
except ImportError:
    AsyncCortexClient = None
    DistanceMetric = None


class KBMedlinePlusService:
    """Ensure MedlinePlus collection exists and run semantic search by query text."""

    def __init__(self) -> None:
        self.host = settings.actian_host
        self.collection = settings.medlineplus_collection
        self.vector_dim = settings.memory_vector_dimension
        self._embedding = EmbeddingService()

    @property
    def is_available(self) -> bool:
        return AsyncCortexClient is not None

    async def ensure_collection(self) -> None:
        """Create the MedlinePlus collection on Actian if it does not exist."""
        if not self.is_available:
            return
        async with AsyncCortexClient(self.host) as client:
            exists = await client.has_collection(self.collection)
            if not exists:
                await client.create_collection(
                    name=self.collection,
                    dimension=self.vector_dim,
                    distance_metric=DistanceMetric.COSINE,
                )

    async def search(self, query_text: str, top_k: int = 5) -> list[dict]:
        """
        Embed query_text, search the MedlinePlus collection, return list of payloads with score.
        Each item is a dict with at least title, url, text, score (and any stored payload fields).
        """
        if not query_text or not (query_text := query_text.strip()):
            return []
        if not self.is_available:
            return []
        query_vector = await self._embedding.embed_text(query_text)
        async with AsyncCortexClient(self.host) as client:
            results = await client.search(
                self.collection,
                query=query_vector,
                top_k=top_k,
                with_payload=True,
            )
        out: list[dict] = []
        for item in results:
            payload = getattr(item, "payload", None) or {}
            score = getattr(item, "score", 0.0)
            out.append({**payload, "score": score})
        return out

    async def batch_upsert(
        self,
        ids: list[int],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        """Insert or update vectors in the MedlinePlus collection. Used by ingest script."""
        if not self.is_available or not ids:
            return
        async with AsyncCortexClient(self.host) as client:
            await client.batch_upsert(self.collection, ids, vectors, payloads)

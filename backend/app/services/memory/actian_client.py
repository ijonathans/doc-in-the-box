from __future__ import annotations

from math import sqrt

from app.core.config import settings

try:
    from cortex import AsyncCortexClient, DistanceMetric
except ImportError:  # pragma: no cover - fallback runtime
    AsyncCortexClient = None
    DistanceMetric = None


class ActianVectorClient:
    def __init__(self) -> None:
        self.host = settings.actian_host
        self.collection = settings.actian_collection_name
        self.vector_dim = settings.memory_vector_dimension
        self._memory_store: dict[str, dict] = {}

    @property
    def is_available(self) -> bool:
        return AsyncCortexClient is not None

    async def ensure_collection(self) -> None:
        if not self.is_available:
            return

        async with AsyncCortexClient(self.host) as client:
            exists = await client.collection_exists(self.collection)
            if not exists:
                await client.create_collection(
                    name=self.collection,
                    dimension=self.vector_dim,
                    distance_metric=DistanceMetric.COSINE,
                )

    async def upsert(self, memory_id: str, vector: list[float], payload: dict) -> None:
        if not self.is_available:
            self._memory_store[memory_id] = {"vector": vector, "payload": payload}
            return

        async with AsyncCortexClient(self.host) as client:
            await client.upsert(self.collection, id=self._to_int_id(memory_id), vector=vector, payload=payload)

    async def search(self, query_vector: list[float], top_k: int, patient_id: int) -> list[dict]:
        if not self.is_available:
            return self._search_memory_store(query_vector=query_vector, top_k=top_k, patient_id=patient_id)

        # Actian Python client filter DSL can be introduced in the next iteration.
        async with AsyncCortexClient(self.host) as client:
            results = await client.search(self.collection, query=query_vector, top_k=max(top_k * 3, top_k))

        filtered: list[dict] = []
        for item in results:
            payload = getattr(item, "payload", {}) or {}
            if str(payload.get("patient_id")) == str(patient_id):
                filtered.append(payload)
            if len(filtered) >= top_k:
                break
        return filtered

    async def list_patient_memories(self, patient_id: int, limit: int = 20) -> list[dict]:
        if not self.is_available:
            rows = []
            for row in self._memory_store.values():
                payload = row["payload"]
                if str(payload.get("patient_id")) == str(patient_id):
                    rows.append(payload)
            return rows[:limit]

        async with AsyncCortexClient(self.host) as client:
            rows = await client.scroll(self.collection, limit=200, cursor=0)
        memories: list[dict] = []
        for row in rows:
            payload = getattr(row, "payload", {}) or {}
            if str(payload.get("patient_id")) == str(patient_id):
                memories.append(payload)
            if len(memories) >= limit:
                break
        return memories

    def _search_memory_store(self, query_vector: list[float], top_k: int, patient_id: int) -> list[dict]:
        scored: list[tuple[float, dict]] = []
        for row in self._memory_store.values():
            payload = row["payload"]
            if str(payload.get("patient_id")) != str(patient_id):
                continue
            score = self._cosine_similarity(query_vector, row["vector"])
            scored.append((score, payload))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [payload for _, payload in scored[:top_k]]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        dot = sum(l * r for l, r in zip(left, right))
        norm_left = sqrt(sum(l * l for l in left)) or 1.0
        norm_right = sqrt(sum(r * r for r in right)) or 1.0
        return dot / (norm_left * norm_right)

    @staticmethod
    def _to_int_id(value: str) -> int:
        return abs(hash(value)) % (10**9)


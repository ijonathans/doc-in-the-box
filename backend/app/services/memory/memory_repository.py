from __future__ import annotations

from datetime import datetime

from app.core.config import settings
from app.services.memory.actian_client import ActianVectorClient
from app.services.memory.embedding_service import EmbeddingService


class MemoryRepository:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_client = ActianVectorClient()

    async def save_memory(
        self,
        memory_type: str,
        patient_id: int,
        text: str,
        metadata: dict | None = None,
    ) -> dict:
        await self.vector_client.ensure_collection()
        memory_id = self._build_memory_id(patient_id=patient_id, memory_type=memory_type)
        payload = {
            "memory_id": memory_id,
            "memory_type": memory_type,
            "patient_id": patient_id,
            "text": text.strip(),
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        vector = await self.embedding_service.embed_text(payload["text"])
        await self.vector_client.upsert(memory_id=memory_id, vector=vector, payload=payload)
        return payload

    async def search_memories(self, patient_id: int, query_text: str, top_k: int | None = None) -> list[dict]:
        query_vector = await self.embedding_service.embed_text(query_text)
        return await self.vector_client.search(
            query_vector=query_vector,
            top_k=top_k or settings.memory_top_k,
            patient_id=patient_id,
        )

    async def list_patient_memories(self, patient_id: int, limit: int = 20) -> list[dict]:
        return await self.vector_client.list_patient_memories(patient_id=patient_id, limit=limit)

    @staticmethod
    def _build_memory_id(patient_id: int, memory_type: str) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"{patient_id}:{memory_type}:{timestamp}"


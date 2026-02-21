from __future__ import annotations

import hashlib

from openai import OpenAI

from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.embedding_model
        self.vector_dim = settings.memory_vector_dimension

    async def embed_text(self, text: str) -> list[float]:
        normalized = (text or "").strip()
        if not normalized:
            return [0.0] * self.vector_dim

        if not self.client:
            return self._deterministic_embedding(normalized)

        response = self.client.embeddings.create(model=self.model, input=normalized)
        vector = list(response.data[0].embedding)
        if len(vector) > self.vector_dim:
            return vector[: self.vector_dim]
        if len(vector) < self.vector_dim:
            return vector + ([0.0] * (self.vector_dim - len(vector)))
        return vector

    def _deterministic_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector = [0.0] * self.vector_dim
        for index in range(self.vector_dim):
            byte = digest[index % len(digest)]
            vector[index] = (byte / 255.0) - 0.5
        return vector


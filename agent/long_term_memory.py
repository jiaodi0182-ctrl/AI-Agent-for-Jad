"""
Long-term memory backed by ChromaDB.
Stores conversation turns as embeddings and retrieves the most
relevant past context for each new query.
"""
import hashlib
import time
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


_DEFAULT_DB_PATH = ".agent_memory"
_COLLECTION = "conversations"


class LongTermMemory:
    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        Path(db_path).mkdir(exist_ok=True)
        self._client = chromadb.PersistentClient(path=db_path)
        self._embed = DefaultEmbeddingFunction()
        self._col = self._client.get_or_create_collection(
            name=_COLLECTION,
            embedding_function=self._embed,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    def save(self, role: str, content: str, metadata: dict | None = None):
        """Persist a single message to long-term storage."""
        if not content or not content.strip():
            return
        doc_id = hashlib.sha256(f"{time.time()}{role}{content}".encode()).hexdigest()[:16]
        meta = {"role": role, "timestamp": time.time(), **(metadata or {})}
        self._col.add(documents=[content], metadatas=[meta], ids=[doc_id])

    def retrieve(self, query: str, n_results: int = 5) -> list[dict]:
        """Return the n most relevant past messages for a query."""
        count = self._col.count()
        if count == 0:
            return []
        n = min(n_results, count)
        results = self._col.query(query_texts=[query], n_results=n)
        memories = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            memories.append({"role": meta.get("role", "unknown"), "content": doc, "timestamp": meta.get("timestamp")})
        return memories

    def format_for_prompt(self, query: str, n_results: int = 4) -> str:
        """Return a formatted string of relevant memories to inject into the system prompt."""
        memories = self.retrieve(query, n_results)
        if not memories:
            return ""
        lines = ["[相关历史记忆]"]
        for m in memories:
            lines.append(f"- [{m['role']}] {m['content'][:200]}")
        return "\n".join(lines)

    def clear(self):
        self._client.delete_collection(_COLLECTION)
        self._col = self._client.get_or_create_collection(
            name=_COLLECTION,
            embedding_function=self._embed,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return self._col.count()

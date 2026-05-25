"""
Long-term memory backed by ChromaDB + BGE embeddings (BAAI/bge-small-zh-v1.5).

BGE is a retrieval-optimized embedding model from BAAI. It runs locally via
ONNX (fastembed), so no API key or torch required.

BGE retrieval convention:
  - Documents are stored as-is.
  - Queries are prefixed with the BGE instruction so the model knows they are
    search queries, not passages. This closes the query/document distribution
    gap and significantly improves recall accuracy.
"""
import hashlib
import time
from pathlib import Path
from typing import List

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from fastembed import TextEmbedding


_DEFAULT_DB_PATH = ".agent_memory"
_BGE_MODEL = "BAAI/bge-small-zh-v1.5"
# Collection name is model-scoped so switching models never causes embedding conflicts
_COLLECTION = "conv_bge_zh_v1_5"
# BGE retrieval instruction (prepend to queries only, not to stored documents)
_QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


class BgeEmbeddingFunction(EmbeddingFunction):
    """ChromaDB-compatible embedding function using BGE via fastembed (ONNX)."""

    def __init__(self, model_name: str = _BGE_MODEL):
        self._model = TextEmbedding(model_name=model_name)
        self._model_name = model_name

    def name(self) -> str:
        return self._model_name

    def __call__(self, input: Documents) -> Embeddings:
        return [vec.tolist() for vec in self._model.embed(list(input))]

    def embed_query(self, input: List[str]) -> Embeddings:
        """Called by ChromaDB for query vectors. Prepends BGE retrieval instruction."""
        prefixed = [f"{_QUERY_INSTRUCTION}{q}" for q in input]
        return [vec.tolist() for vec in self._model.embed(prefixed)]


class LongTermMemory:
    def __init__(self, db_path: str = _DEFAULT_DB_PATH, model: str = _BGE_MODEL):
        Path(db_path).mkdir(exist_ok=True)
        self._client = chromadb.PersistentClient(path=db_path)
        self._embed = BgeEmbeddingFunction(model_name=model)
        self._col = self._client.get_or_create_collection(
            name=_COLLECTION,
            embedding_function=self._embed,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------

    def save(self, role: str, content: str, metadata: dict | None = None):
        """Persist a single message as a BGE embedding."""
        if not content or not content.strip():
            return
        doc_id = hashlib.sha256(f"{time.time()}{role}{content}".encode()).hexdigest()[:16]
        meta = {"role": role, "timestamp": time.time(), **(metadata or {})}
        self._col.add(documents=[content], metadatas=[meta], ids=[doc_id])

    def retrieve(self, query: str, n_results: int = 5) -> list[dict]:
        """
        Return the n most semantically relevant past messages for a query.
        The query is embedded with the BGE retrieval instruction for best recall.
        """
        count = self._col.count()
        if count == 0:
            return []
        n = min(n_results, count)
        # ChromaDB routes query_texts through embed_query(), which adds the BGE instruction
        results = self._col.query(query_texts=[query], n_results=n)
        memories = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            memories.append({
                "role": meta.get("role", "unknown"),
                "content": doc,
                "timestamp": meta.get("timestamp"),
            })
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

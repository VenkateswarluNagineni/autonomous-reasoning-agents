import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    HAS_SBERT = True
except ImportError:
    HAS_SBERT = False

from src.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """
    In-memory / Persistent Vector Store backed by Sentence-Transformers embeddings
    and exact cosine similarity search.
    """

    def __init__(self, index_path: str | None = None):
        self.index_path = Path(index_path or settings.vector_index_path)
        self.dimension = settings.vector_dimension
        self.vectors: list[np.ndarray] = []
        self.documents: list[str] = []
        self.metadatas: list[dict[str, Any]] = []
        self._model = None
        self._load_index()

    @property
    def model(self):
        if self._model is None:
            if HAS_SBERT:
                logger.info(f"Loading SentenceTransformer model: {settings.embedding_model_name}")
                self._model = SentenceTransformer(settings.embedding_model_name)
            else:
                logger.warning(
                    "sentence-transformers not installed or unavailable. Using deterministic hash fallback."
                )
                self._model = "fallback"
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        """
        Encode text strings into high-dimensional vector embeddings.
        """
        if self.model == "fallback":
            # Deterministic mock embedding generator for CI/CD or local test speed
            np.random.seed([abs(hash(t)) % (2**32) for t in texts])
            vecs = np.random.normal(0, 1, (len(texts), self.dimension))
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            return vecs / (norms + 1e-10)

        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings

    def add_texts(self, texts: list[str], metadatas: list[dict[str, Any]] | None = None) -> list[int]:
        """
        Embed and index a list of text chunks with optional metadata.
        """
        if not texts:
            return []

        if metadatas is None:
            metadatas = [{} for _ in texts]

        embeddings = self.encode(texts)
        start_id = len(self.documents)
        ids = []

        for i, (text, emb, meta) in enumerate(zip(texts, embeddings, metadatas, strict=True)):
            self.documents.append(text)
            self.vectors.append(emb)
            self.metadatas.append(meta)
            ids.append(start_id + i)

        self._save_index()
        logger.info(f"Indexed {len(texts)} chunks into VectorStore.")
        return ids

    def similarity_search(
        self, query: str, top_k: int = 5, filter_dict: dict[str, Any] | None = None
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """
        Execute cosine similarity search for a query against stored document vectors.
        Returns list of (document_text, similarity_score, metadata).
        """
        if not self.documents:
            return []

        query_vec = self.encode([query])[0]

        # Filter indices if metadata filter is provided
        valid_indices = []
        if filter_dict:
            for idx, meta in enumerate(self.metadatas):
                match = all(meta.get(k) == v for k, v in filter_dict.items())
                if match:
                    valid_indices.append(idx)
        else:
            valid_indices = list(range(len(self.documents)))

        if not valid_indices:
            return []

        matrix = np.array([self.vectors[i] for i in valid_indices])
        scores = np.dot(matrix, query_vec)  # Vectors are already unit normalized

        # Get top_k indices
        top_k = min(top_k, len(scores))
        best_local_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for loc_idx in best_local_indices:
            global_idx = valid_indices[loc_idx]
            score = float(scores[loc_idx])
            results.append((self.documents[global_idx], score, self.metadatas[global_idx]))

        return results

    def _save_index(self):
        """Persist index metadata and vectors to disk."""
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "documents": self.documents,
                "metadatas": self.metadatas,
                "vectors": [v.tolist() for v in self.vectors]
            }
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save VectorStore index: {e}")

    def _load_index(self):
        """Load persisted index from disk if present."""
        if self.index_path.exists():
            try:
                with open(self.index_path, encoding="utf-8") as f:
                    data = json.load(f)
                self.documents = data.get("documents", [])
                self.metadatas = data.get("metadatas", [])
                self.vectors = [np.array(v, dtype=np.float32) for v in data.get("vectors", [])]
                logger.info(f"Loaded {len(self.documents)} indexed vectors from disk.")
            except Exception as e:
                logger.error(f"Failed to load VectorStore index: {e}")


# Singleton instance
vector_store = VectorStore()

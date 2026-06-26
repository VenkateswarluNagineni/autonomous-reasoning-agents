from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.memory.vector_store import vector_store


class RetrievedContext(BaseModel):
    """Structured context retrieved from vector store."""
    content: str = Field(..., description="Text content chunk")
    score: float = Field(..., description="Cosine similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source document metadata")


class RAGRetriever:
    """
    High-level RAG context retrieval engine providing score filtering
    and prompt formatting utilities.
    """

    def __init__(self, store=vector_store, min_score_threshold: float = 0.25):
        self.store = store
        self.min_score_threshold = min_score_threshold

    def retrieve(self, query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[RetrievedContext]:
        """
        Query vector store and return structured contexts meeting score threshold.
        """
        raw_results = self.store.similarity_search(query, top_k=top_k, filter_dict=filter_dict)
        retrieved = []
        for text, score, meta in raw_results:
            if score >= self.min_score_threshold:
                retrieved.append(RetrievedContext(content=text, score=score, metadata=meta))
        return retrieved

    def format_as_prompt_context(self, contexts: List[RetrievedContext]) -> str:
        """
        Format retrieved context chunks into clean markdown blocks for LLM injection.
        """
        if not contexts:
            return "No relevant external domain documents retrieved."

        blocks = []
        for i, ctx in enumerate(contexts, 1):
            source = ctx.metadata.get("source", "Unknown Document")
            domain_precision = ctx.metadata.get("domain_precision", "N/A")
            blocks.append(f"### [Context {i}] Source: {source} (Confidence: {ctx.score:.2f})\n{ctx.content}")

        return "\n\n".join(blocks)


retriever = RAGRetriever()

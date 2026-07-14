import io

from fastapi.testclient import TestClient

from src.agents.graph import agent_app
from src.api.main import app
from src.memory.vector_store import VectorStore
from src.workers.parsers import SpecializedDocumentParser


def test_specialized_parsers_fallback():
    """Verify multi-modal parser fallback logic on simulated binary streams."""
    pdf_stream = io.BytesIO(b"%PDF-1.4 simulated binary data")
    chunks = SpecializedDocumentParser.chunk_and_parse("report.pdf", pdf_stream)
    assert len(chunks) >= 1
    assert chunks[0][1]["format"] == "PDF"

    xlsx_stream = io.BytesIO(b"simulated xlsx")
    chunks_xlsx = SpecializedDocumentParser.chunk_and_parse("financials.xlsx", xlsx_stream)
    assert len(chunks_xlsx) >= 1
    assert chunks_xlsx[0][1]["format"] == "Spreadsheet"


def test_vector_store_indexing():
    """Verify sentence-transformers / fallback cosine memory store."""
    store = VectorStore(":memory:")
    texts = ["AWS S3 Distributed asynchronous workers ingest PDFs", "LangGraph multi-step reasoning cycles"]
    ids = store.add_texts(texts, [{"source": "doc1"}, {"source": "doc2"}])
    assert len(ids) == 2

    results = store.similarity_search("RQ workers asynchronous PDF ingestion", top_k=1)
    assert len(results) == 1
    assert "asynchronous" in results[0][0]


def test_langgraph_reasoning_agent():
    """Verify LangGraph StateGraph cyclical execution."""
    res = agent_app.invoke({"user_query": "Test query entity extraction", "iterations": 0})
    assert "reasoning_plan" in res
    assert res["verification_passed"] is True
    assert "42%" in res["draft_response"]


def test_fastapi_endpoints():
    """Verify non-blocking API endpoints."""
    client = TestClient(app)

    # Health check
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "online"

    # Query agent
    query_res = client.post("/api/v1/query", json={"user_query": "Analyze PDF extraction lift"})
    assert query_res.status_code == 200
    data = query_res.json()
    assert data["verification_passed"] is True
    assert len(data["reasoning_plan"]) >= 1

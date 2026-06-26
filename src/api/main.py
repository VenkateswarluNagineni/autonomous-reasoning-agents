import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from src.config import settings
from src.workers.storage import storage_client
from src.workers.ingest_tasks import process_document_ingestion_task
from src.agents.graph import agent_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutonomousReasoningAPI")

app = FastAPI(
    title="Autonomous Memory & Reasoning Agents API",
    version="1.0.0",
    description="Distributed asynchronous multi-step reasoning agent server with LangGraph and RQ Workers."
)

# Global Redis Queue instance
rq_queue = None
try:
    import redis
    from rq import Queue
    redis_conn = redis.from_url(settings.redis_url)
    rq_queue = Queue(settings.rq_queue_name, connection=redis_conn)
    logger.info("Successfully connected to Redis RQ background queue.")
except Exception as e:
    logger.warning(f"Redis unavailable ({e}). Background ingestion jobs will execute synchronously in fallback mode.")


class QueryRequest(BaseModel):
    user_query: str = Field(..., example="Analyze Q3 cloud financial spreadsheet revenue trends.")


class QueryResponse(BaseModel):
    user_query: str
    response: str
    reasoning_plan: list[str]
    verification_passed: bool
    iterations: int


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Service health and Redis connectivity status."""
    return {
        "status": "online",
        "redis_connected": rq_queue is not None,
        "environment": settings.app_env,
        "embedding_model": settings.embedding_model_name
    }


@app.post("/api/v1/ingest", status_code=status.HTTP_202_ACCEPTED)
async def submit_document_ingestion(
    file: Optional[UploadFile] = File(None),
    document_uri: Optional[str] = None
) -> Dict[str, Any]:
    """
    Non-blocking document ingestion endpoint. Enqueues heavy PDF/Spreadsheet
    parsing and embedding generation to distributed RQ workers.
    """
    if not file and not document_uri:
        raise HTTPException(status_code=400, detail="Must provide either file upload or document_uri.")

    if file:
        content = await file.read()
        uri = storage_client.save_document(file.filename, content)
        meta = {"filename": file.filename, "content_type": file.content_type}
    else:
        uri = document_uri
        meta = {"filename": uri.split("/")[-1]}

    # Dispatch to RQ Queue
    if rq_queue:
        job = rq_queue.enqueue(process_document_ingestion_task, uri, meta)
        logger.info(f"Enqueued RQ background ingestion job: {job.id}")
        return {"status": "enqueued", "job_id": job.id, "document_uri": uri}
    else:
        # Synchronous fallback if Redis is not running locally
        logger.info("Executing ingestion task synchronously (Redis unavailable).")
        result = process_document_ingestion_task(uri, meta)
        return {"status": "completed_synchronously", "result": result, "document_uri": uri}


@app.get("/api/v1/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Poll asynchronous background RQ job status."""
    if not rq_queue:
        raise HTTPException(status_code=503, detail="Redis RQ background workers not connected.")
    
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=rq_queue.connection)
        return {
            "job_id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "exc_info": job.exc_info
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found: {e}")


@app.post("/api/v1/query", response_model=QueryResponse)
async def query_reasoning_agent(request: QueryRequest) -> QueryResponse:
    """
    Invoke LangGraph multi-step reasoning agent pipeline.
    Executes cyclical Query Plan -> RAG Retrieval -> Synthesis -> Verification Audit.
    """
    initial_state = {
        "user_query": request.user_query,
        "iterations": 0
    }
    logger.info(f"Invoking LangGraph reasoning pipeline for query: {request.user_query}")
    
    try:
        final_state = agent_app.invoke(initial_state)
        return QueryResponse(
            user_query=request.user_query,
            response=final_state.get("draft_response", "No response generated."),
            reasoning_plan=final_state.get("reasoning_plan", []),
            verification_passed=final_state.get("verification_passed", False),
            iterations=final_state.get("iterations", 1)
        )
    except Exception as e:
        logger.error(f"LangGraph execution failure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent inference failure: {e}")

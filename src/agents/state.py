from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class AgentState(TypedDict):
    """
    LangGraph State dictionary tracking multi-step reasoning cycles.
    """
    user_query: str
    reasoning_plan: List[str]
    retrieved_context: str
    extracted_domain_entities: Dict[str, Any]
    draft_response: str
    verification_passed: bool
    iterations: int
    error: Optional[str]

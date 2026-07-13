from typing import Any, TypedDict


class AgentState(TypedDict):
    """
    LangGraph State dictionary tracking multi-step reasoning cycles.
    """
    user_query: str
    reasoning_plan: list[str]
    retrieved_context: str
    extracted_domain_entities: dict[str, Any]
    draft_response: str
    verification_passed: bool
    iterations: int
    error: str | None

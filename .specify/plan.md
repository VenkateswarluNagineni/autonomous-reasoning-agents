# Technical Restructuring & Implementation Plan (`plan.md`)

## 1. Architectural Restructuring Objectives
1. **Separation of Concerns**: Ensure `graph.py` only handles graph routing and node execution logic, `retriever.py` isolates embedding queries, and `parsers.py` manages document ingestion without side effects.
2. **Deterministic State Handling**: Enforce strict type annotations (`AgentState`) across all node handlers (`analyze_query_node`, `retrieve_context_node`, `synthesize_extraction_node`, `verify_precision_node`).
3. **Loop Bounding & Safety**: Verify `should_continue_router` explicitly checks `state.get("iterations", 0) >= 3` before routing back to `retrieve`.

## 2. Code Restructuring Blueprint
- `src/agents/graph.py`: Maintain clean node definitions. Ensure `analyze_query_node` increments `iterations`.
- `src/api/main.py`: Ensure `/v1/agents/run` validates incoming JSON payloads cleanly and catches runtime exceptions without leaking internal stack traces.
- `src/workers/parsers.py`: Maintain clean, standalone chunking functions without global mutation.
- `eval/benchmark.py`: Execute end-to-end numerical verification confirming the `42%` precision lift over baseline.

## 3. DevSecOps Integration Checkpoints
- **SAST**: `Ruff -S check .` and `CodeQL` / `Semgrep` inside `.github/workflows/devsecops.yml`.
- **SCA**: `pip-audit` validating zero CVEs across `requirements.txt`.

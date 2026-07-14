# Autonomous Reasoning Agents Constitution (`github/spec-kit` Protocol)

## 1. Core Engineering & Safety Principles
1. **Deterministic State Graph Invariants**: All autonomous agent reasoning flows MUST be modeled as explicit, typed state transitions inside `StateGraph(AgentState)` (`langgraph`). No ad-hoc recursion or unbounded global variables.
2. **Zero Code Injection & Execution Boundaries**: Under no circumstances shall dynamic string evaluation (`eval()`, `exec()`) or unverified system calls (`subprocess`) be introduced inside graph nodes (`analyze`, `retrieve`, `synthesize`, `verify`) or API handlers.
3. **Async Memory Retrieval & Non-Blocking I/O**: Vector store queries (`retriever.retrieve`) and document ingestion workers (`parsers.py`) must execute asynchronously or inside thread/process pools without blocking the primary event loop.
4. **Self-Correction & Bounded Loops**: All cyclical edge transitions (`should_continue_router`) MUST enforce a maximum iteration ceiling (`iterations >= 3`) to prevent infinite reasoning loops and resource exhaustion.
5. **Continuous Verification Gate**: All modifications to graph logic, memory indexing, or API endpoints MUST pass the `Ruff -S` security linter and achieve 100% pass rates across `tests/test_pipeline.py` and `eval/benchmark.py`.

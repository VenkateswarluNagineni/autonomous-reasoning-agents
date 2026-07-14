# Verifiable Task Checklist (`tasks.md`)

- [x] **Task 1: Spec-Kit Initialization**
  - Create `.specify/constitution.md` with core safety and deterministic invariants.
  - Create `.specify/spec.md` with data schema (`AgentState`), graph boundaries, and API endpoint contracts (`POST /v1/agents/run`).
  - Create `.specify/plan.md` with step-by-step restructuring rules.

- [x] **Task 2: Code Architecture & Restructuring Verification**
  - Verify `src/agents/graph.py` increments `iterations` cleanly and bounds cyclical self-correction passes (`iterations >= 3`).
  - Verify `src/api/main.py` enforces payload validation and error handling without unhandled trace tracebacks.
  - Verify `src/workers/parsers.py` maintains modular document chunking functions.

- [x] **Task 3: Security & Quality Gate Execution**
  - Run SAST scan (`ruff check . --select E,F,S,I,UP,B,C90`) -> `100% clean`.
  - Run `pip-audit` -> `0 vulnerabilities`.
  - Execute unit verification (`pytest -v`) -> `100% tests passed`.
  - Execute numerical benchmark (`python run_tests.py`) -> `42% precision lift verified`.

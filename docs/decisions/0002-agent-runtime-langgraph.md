---
status: accepted
date: 2026-11-27
decision-makers: lodekit-agents owner, lead; adopted by Naki (maintainer)
---

# ADR-002: Agent runtime: LangGraph as the only runtime, lodekit-agents as the DX layer

Accepted 2026-11-27 by the lodekit-agents owner after spike S7b, and adopted by the lead.

## Context and problem statement

`lodekit-agents` should make agents easy to compose without building its own runtime.

- LangGraph provides state, execution, checkpointing, streaming and interrupts.
- `langchain-core` provides models, messages and tools.
- LangChain 1.x offers `create_agent` with middleware.

Which runtime should `lodekit-agents` build on, and what value does it add?

## Considered options

- LangGraph as the only runtime, with `lodekit-agents` as a DX layer on `create_agent` + middleware
- An own runtime
- A thin `create_agent` wrapper
- CrewAI, AutoGen or PydanticAI

## Decision outcome

Chosen option: **LangGraph as the only runtime; `lodekit-agents` as the DX layer.**

1. **LangGraph is the only runtime.** Every `Agent` and `Team` compiles to a LangGraph graph.
   `agent.graph` is public and serves as the escape hatch.
2. **langchain-core is the base** for `BaseChatModel`, messages and `BaseTool`. There are no
   parallel abstractions.
3. **What lodekit-agents adds is developer experience:**
   - `Agent`, `Team` and `ask()` / `aask()`;
   - a tool registry with policy;
   - controlled state with write guards;
   - limits;
   - a unified `Result` and typed events and hooks.
4. **lodekit-agents runs without DuckDB.** The core never imports `duckdb`, and a contract test
   enforces this.
5. **No LLM provider is hard-wired.** A model is a `BaseChatModel` instance or a `"provider:model"`
   string. Providers are optional extras (`openai`, `anthropic`, `ollama`, `all`).
6. **`Agent` builds on `create_agent` + lodekit middleware; `Team` builds directly on
   `StateGraph`.**
   - Limits, policy and write guards are middleware.
   - The supervisor pattern is implemented as "agents as tools", because `langgraph-supervisor` is
     archived.
   - This adds the core dependency `langchain>=1.5,<2`, which effectively caps `langgraph` at
     `<1.3`, because langchain 1.5.2 requires `langgraph>=1.2.12,<1.3`.
7. **State.** The public `State` stays Pydantic. Internally it is a TypedDict plus a
   `PydanticValidationMiddleware`:
   - `create_agent` silently converts a Pydantic `state_schema` to a TypedDict, so a regression
     test guards against silent loss of validation;
   - a missing `messages` field raises `ConfigError`.
8. **Limits.** An own `LimitsMiddleware` raises `LimitExceeded(partial_state)`, and the run can be
   resumed via `invoke(None)`. The write guard protects state only, not side effects.
9. **MCP (later, M4).** Use `langchain[mcp]` or the MCP SDK 2.x directly. `langchain-mcp-adapters`
   is archived and pins `mcp<2`.

### Amendment 2026-11-27 (decision D1b)

lodekit ships **no own DuckDB wrappers**. The originally planned `[duckdb]` extra and the read-only
DuckDB SQL tool are therefore dropped. Examples use a plain read-only data tool over exported
Parquet/CSV files instead.

### Spike S7b evidence

- All 22 offline checks are green.
- `langsmith` and `langgraph-sdk` are mandatory transitive dependencies (39 packages without
  providers). This is documented, telemetry is off by default, and the CI `dependency-tree` job
  tracks them.
- The public names `Agent`, `Team` and `ask` do not collide with `langchain`, `langchain-core` or
  `langgraph` exports. `State` is used instead of `AgentState`, to avoid confusion with
  `langchain.agents.AgentState`.

### Consequences

- Good:
  - a small codebase with all LangGraph features available;
  - LangChain 1.x follows SemVer with LTS.
- Bad: LangGraph is coupled to the version window that `langchain` allows (currently 1.2.x).
  This is mitigated by:
  - upper-bounded pins;
  - contract tests;
  - a nightly run against the latest versions.
- Bad: the value over plain `create_agent` must be clearly visible, through registry and policy,
  state guards, teams and ecosystem integration. The docs explain how `lodekit.agents` differs
  from `langchain.agents`.

### Confirmation

- A contract test checks that `agent.graph` is a compiled LangGraph graph.
- A contract test checks that `lodekit.agents` imports without `duckdb`.
- A regression test guards Pydantic state validation.
- The CI `lowest-direct` job and the dependency-tree report.

## Pros and cons of the options

- **An own runtime.** Rejected: it duplicates LangGraph and has a large maintenance surface.
- **A thin `create_agent` wrapper.** Rejected: it adds too little value.
- **CrewAI, AutoGen or PydanticAI.** Outside the architecture decision for the LangChain and
  LangGraph ecosystem.

# ADR-021 — LLM Provider Abstraction

## Status

Accepted

> **Re-baseline note (2026-09-28).**
>
> - *Current state.* The Qwen3:8B model named below was the Sprint 11 choice. The current
>   default is **`gemma3:4b`** (`OLLAMA_MODEL`, `src/core/config.py`, `.env.example`).
>   `src/llm/llm_factory.py` registers exactly one provider, `"ollama"` → `OllamaClient`.
> - *Sprint 16 builds on this ADR.* Sprint 16 Phase 1 (AI Provider Abstraction) extends
>   `BaseLLM` / `LLMFactory` rather than creating a parallel framework, unless its audit
>   proves this abstraction inadequate. Scope: Ollama and Google Cloud / Gemini, selected by
>   configuration; future providers (e.g. Groq) as isolated adapters; request/response
>   normalization; timeouts, retries and transient-failure handling; provider exceptions
>   mapped to stable application errors; logging, observability and provider/model metadata;
>   backward compatibility with current AI workflows (ADR-025 job lifecycle, ADR-027
>   privacy-safe context).
> - *Decision record.* Any change to the provider interface or selection mechanism made in
>   Sprint 16 is recorded in a follow-up ADR that amends this one. The decision text below
>   is unchanged.

---

## Context

Sprint 11 introduces AI-powered business insights into AnalystGPT Enterprise.

The AI subsystem requires a Large Language Model (LLM) to generate:

- Executive summaries
- Business recommendations
- Explanations
- Business narratives

A direct dependency on a single provider would tightly couple the application to one implementation and make future migration difficult.

The application should remain independent of any specific AI vendor.

---

## Decision

Introduce an abstraction layer for all language model providers.

The architecture consists of:

```
AI Engine
      │
      ▼
BaseLLM
      │
      ▼
LLMFactory
      │
      ▼
OllamaClient
      │
      ▼
Local Ollama Server
      │
      ▼
Qwen3:8B
```

The AI engines communicate only with the BaseLLM interface.

Provider creation is delegated to LLMFactory.

Current provider:

- Ollama
- Local execution
- Qwen3:8B

Future providers can be added without modifying the AI subsystem.

Examples include:

- OpenAI
- Azure OpenAI
- Anthropic Claude
- Google Gemini
- LM Studio
- vLLM
- Local HuggingFace models

---

## Consequences

### Advantages

- Loose coupling
- Dependency inversion
- Easier testing using fake LLM implementations
- Supports multiple providers
- Enables future cloud migration
- Keeps AI engines provider-independent

### Trade-offs

- Slight increase in architectural complexity
- Factory maintenance as providers increase

---

## Alternatives Considered

### Direct Ollama calls

Rejected because it tightly couples business logic to Ollama.

### AI logic inside reporting module

Rejected because AI is a separate subsystem with independent responsibilities.

### Static utility functions

Rejected because they prevent dependency injection and mocking.

---

## Implementation

Components introduced:

```
src/llm/

base_llm.py
llm_factory.py
ollama_client.py
prompt_builder.py
report_serializer.py
response_parser.py
```

AI subsystem:

```
src/ai/

ai_manager.py
executive_summary_engine.py
recommendation_engine.py
explanation_engine.py
narrative_engine.py
```

---

## Result

The AnalystGPT Enterprise AI subsystem is fully decoupled from any specific language model implementation.

Future providers can be added with minimal code changes while preserving the existing architecture.
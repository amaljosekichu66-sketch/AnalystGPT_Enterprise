# ADR-021 — LLM Provider Abstraction

## Status

Accepted

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
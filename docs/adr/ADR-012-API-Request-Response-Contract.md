# ADR-012 — API Request & Response Contracts

**Status:** Accepted

**Date:** 23 July 2026

**Sprint:** Sprint 8 — REST API Integration

**Version:** v8.0.0

---

# Context

Introducing a REST API Layer required a standardized mechanism
for exchanging data between external clients and AnalystGPT Enterprise.

Without formal contracts:

- Clients become dependent on implementation details.
- API evolution becomes unpredictable.
- Validation becomes inconsistent.
- Documentation cannot be generated automatically.

A contract-first approach was selected to preserve long-term API stability.

---

# Decision

Adopt strongly typed request and response models using Pydantic.

Every endpoint must:

- Accept a defined request model.
- Return a defined response model.
- Validate requests before business execution.
- Serialize responses consistently.

The API contract becomes the public interface of the application.

---

# Contract Flow

```text
HTTP Request
      │
      ▼
PipelineRequest
      │
      ▼
Application.run()
      │
      ▼
PipelineResult
      │
      ▼
PipelineResponse
      │
      ▼
HTTP Response
```

---

# Request Contracts

Current request models include:

- PipelineRequest

Responsibilities:

- Validate input
- Define required fields
- Reject invalid requests
- Provide automatic documentation

---

# Response Contracts

Current response models include:

- APIResponse
- RootResponse
- HealthResponse
- VersionResponse
- PipelineResponse

Responsibilities:

- Stable output
- Consistent serialization
- Strong typing
- Automatic OpenAPI generation

---

# Consequences

## Positive

- Stable client interfaces.
- Automatic validation.
- Consistent API responses.
- Simplified documentation.
- Improved maintainability.
- Easier automated testing.
- Backward compatibility becomes manageable.

---

## Negative

- Contract changes require careful version management.
- Additional models increase repository size.
- Public interfaces require long-term maintenance.

---

# Alternatives Considered

## Dictionary Responses

Rejected.

Reason:

Weak typing increases maintenance risk and reduces documentation quality.

---

## Untyped Requests

Rejected.

Reason:

Validation would become inconsistent and error-prone.

---

## Direct DataFrame Exchange

Rejected.

Reason:

Internal implementation details should never be exposed through public APIs.

---

# Design Principles Preserved

- Contract-driven Development
- Strong Typing
- Separation of Concerns
- Stable Interfaces
- API-first Architecture
- Backward Compatibility

---

# Implementation Impact

New models introduced:

- PipelineRequest
- PipelineResponse
- RootResponse
- HealthResponse
- VersionResponse
- APIResponse

These contracts define the public interface while allowing
internal implementations to evolve independently.

---

# Validation

Contracts validated through:

- Request Validation
- Response Validation
- Swagger UI
- OpenAPI Specification
- Integration Tests
- Endpoint Tests

All validations completed successfully.

---

# Future Impact

Future endpoints should continue using:

- Strong typing
- Stable contracts
- Versioned interfaces
- Pydantic validation

Breaking changes should require:

- New ADR
- Documentation updates
- Automated tests
- Version increment

---

# Engineering Guidance

Public contracts are long-term commitments.

Implementation details may evolve, but stable interfaces
must remain predictable for external consumers.

---

**Decision:** Accepted

**Review Status:** Active
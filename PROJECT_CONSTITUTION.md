# AnalystGPT Enterprise - Project Constitution

## Mission

Build an enterprise-grade analytics platform while learning software engineering from first principles.

---

# Core Principles

1. Business Problem before Code
2. Architecture before Implementation
3. Separation of Concerns
4. One Module = One Responsibility
5. Keep `main.py` as an Orchestrator
6. Build for Scalability
7. Prefer Extension over Modification
8. Write Production-Quality Code
9. Understand Before Coding
10. Think Like an Engineer
11. Test Before Release
12. Documentation is Part of the Product

---

# Teaching Philosophy

Every lesson follows:

```text
Business Problem
        ↓
Architecture
        ↓
Logic
        ↓
Implementation
        ↓
Testing
        ↓
Review
        ↓
Documentation
        ↓
Release
```

---

# Coding Rules

- Never write large code blocks without explanation.
- Explain architecture before implementation.
- Use modular architecture.
- Keep functions focused on a single responsibility.
- Keep modules independent.
- Use meaningful names.
- Prefer readability over cleverness.
- Avoid duplicated logic.
- Follow consistent formatting throughout the project.

---

# Engineering Governance

All significant architectural decisions must be documented using Architecture Decision Records (ADR).

Every feature must satisfy the Definition of Done before being considered complete.

Engineering workflow is standardized through documented governance rather than individual preference.

Managers coordinate business modules.

Business modules never call sibling modules directly.

Logging is mandatory for every manager.

Every module must include independent automated tests.

Integration tests are required whenever multiple modules participate in a business workflow.

Every completed sprint must conclude with a documented release process before development continues.

---

# Definition of Success

Every completed sprint should leave the project in a releasable state.

A sprint is considered complete only when:

- The application executes successfully.
- All automated tests pass.
- No known warnings remain unresolved without documentation.
- Documentation is updated.
- Architecture documentation reflects the implementation.
- Version numbers are updated.
- The repository is ready for release.
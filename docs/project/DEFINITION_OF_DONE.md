# AnalystGPT Enterprise Definition of Done (DoD)

## Purpose

The Definition of Done establishes the minimum quality standard required before any feature, sprint, or release is considered complete.

A task is not complete simply because the code works.

It is complete only when it satisfies the engineering standards defined below.

---

# Business

- Business problem understood
- Requirements clarified
- Business value identified

---

# Architecture

- Architecture reviewed
- Module responsibilities clearly defined
- Stable contracts respected
- Dependency direction preserved
- Business logic remains independent of infrastructure
- ADR created or updated if required

---

# Implementation

- Code implemented
- Engineering principles followed
- Shared configuration used where applicable
- Existing public interfaces preserved unless intentionally changed
- No unnecessary complexity introduced

---

# Testing

- Smoke testing completed
- Edge cases considered
- Failure scenarios considered

### Infrastructure Validation (when applicable)

- Database initialization verified
- Repository operations validated
- Cross-database compatibility validated

---

# Documentation

- Architecture updated (if required)
- ADR updated (if required)
- Changelog updated
- Project Journal updated
- Roadmap updated
- PROJECT_STATE updated
- Lessons Learned updated (if applicable)

---

# Code Review

- Pull Request reviewed
- Review comments resolved
- Code approved
- Code Review Checklist completed

---

# Git

- Meaningful commit history
- Appropriate branch naming
- Successfully merged
- Release tag created (for sprint releases)

---

# Release Readiness

- Project version synchronized across documentation

A feature is considered complete only after all applicable checklist items have been satisfied.

Engineering quality always takes precedence over implementation speed.
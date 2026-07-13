# AnalystGPT Enterprise Documentation Standards

## Purpose

This document defines the responsibility of every documentation file within AnalystGPT Enterprise.

Each document has one clearly defined responsibility.

Avoid duplicating information across multiple documents.

---

# Documentation Principles

Documentation should be:

- Accurate
- Concise
- Maintainable
- Discoverable
- Version controlled

Every document should answer one specific question.

---

# Documentation Responsibilities

## README.md

Purpose

Project overview.

Contains:

- Project description
- Features
- Setup instructions
- Quick start guide

Do not include detailed architecture or sprint history.

---

## PROJECT_CONSTITUTION.md

Purpose

Permanent engineering principles.

Contains:

- Engineering philosophy
- Architectural principles
- Coding philosophy

Changes rarely.

---

## ARCHITECTURE.md

Purpose

Explain how the system is designed.

Contains:

- Module responsibilities
- Data flow
- System architecture
- Stable contracts
- Shared infrastructure

Update only when architecture changes.

---

## ADRs

Purpose

Record important architectural decisions.

Contains:

- Context
- Decision
- Alternatives
- Consequences

Never duplicate Architecture.md.

Architecture explains the current design.

ADRs explain why the design exists.

---

## CHANGELOG.md

Purpose

Track technical changes.

Contains:

- Features
- Improvements
- Refactoring
- Bug fixes

Keep entries concise and chronological.

---

## PROJECT_JOURNAL.md

Purpose

Engineering diary.

Contains:

- Sprint summaries
- Lessons learned
- Progress made

Updated every sprint.

---

## LESSONS_LEARNED.md

Purpose

Long-term engineering knowledge.

Contains:

- Engineering concepts
- Best practices
- Reusable lessons

Avoid sprint-specific notes.

---

## ROADMAP.md

Purpose

Track project progress.

Contains:

- Completed sprints
- Current sprint
- Upcoming work

---

## PROJECT_STATE.md

Purpose

Current source of truth.

Contains:

- Current sprint
- Architecture status
- Current module
- Repository status
- Current blockers

Always reflects the latest project state.

---

# Documentation Rules

Before creating a new document, ask:

- Does this information already exist?
- Which document owns this responsibility?
- Will this create duplication?

If another document already owns the information, update that document instead.

---

# Documentation Philosophy

Documentation should preserve engineering knowledge.

Optimize for future engineers who have never seen the project before.
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
- Consistent

Every document should answer one specific question.

---

# Documentation Responsibilities

## README.md

**Purpose**

Project overview.

**Contains:**

- Project description
- Features
- Setup instructions
- Quick start guide

**Do not include:**

- Detailed architecture
- Sprint history
- Engineering governance
- Internal implementation details

---

## PROJECT_CONSTITUTION.md

**Purpose**

Permanent engineering principles.

**Contains:**

- Engineering philosophy
- Architectural principles
- Coding philosophy

Changes rarely.

---

## ARCHITECTURE.md

**Purpose**

Explain how the system is designed.

**Contains:**

- Module responsibilities
- Data flow
- System architecture
- Stable contracts
- Shared infrastructure

Update only when architecture changes.

---

## ADRs

**Purpose**

Record important architectural decisions.

**Contains:**

- Context
- Decision
- Alternatives
- Consequences

Never duplicate Architecture.md.

Architecture explains the current design.

ADRs explain why the design exists.

---

## ENGINEERING_PLAYBOOK.md

**Purpose**

Defines the standard engineering workflow.

**Contains:**

- Development workflow
- Git workflow
- Testing workflow
- Release workflow
- Code review expectations
- Definition of Done

Update when engineering practices change.

---

## ENGINEERING_OPERATING_MANUAL.md

**Purpose**

Operational reference for maintaining the project.

**Contains:**

- Engineering procedures
- Repository operations
- Development conventions
- Release operations

Update when operational processes change.

---

## CHANGELOG.md

**Purpose**

Track technical changes.

**Contains:**

- Features
- Improvements
- Refactoring
- Bug fixes

Keep entries concise and chronological.

---

## PROJECT_JOURNAL.md

**Purpose**

Engineering diary.

**Contains:**

- Sprint summaries
- Major engineering milestones
- Lessons learned
- Progress made

Updated every sprint.

---

## LESSONS_LEARNED.md

**Purpose**

Long-term engineering knowledge.

**Contains:**

- Engineering concepts
- Best practices
- Reusable lessons

Avoid recording implementation history or release notes. Capture only engineering concepts that remain valuable beyond a single sprint.

---

## ROADMAP.md

**Purpose**

Track project progress.

**Contains:**

- Completed sprints
- Current sprint
- Upcoming work
- Planned future milestones

---

## PROJECT_STATE.md

**Purpose**

Current source of truth.

**Contains:**

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
- Has another document become the better owner of this information?

If another document already owns the information, update that document instead.

---

# Documentation Philosophy

Documentation should preserve engineering knowledge and reduce onboarding time for future contributors.

Optimize for future engineers who have never seen the project before.
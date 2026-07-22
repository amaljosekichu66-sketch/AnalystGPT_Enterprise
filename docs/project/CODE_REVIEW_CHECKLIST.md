# AnalystGPT Enterprise Code Review Checklist

## Purpose

This checklist standardizes code reviews across AnalystGPT Enterprise.

Every Pull Request should be reviewed against these criteria before approval.

---

# 1. Business Requirements

- Does the implementation solve the intended business problem?
- Does it satisfy the documented requirements?
- Is unnecessary functionality avoided?

---

# 2. Architecture

- Does the implementation respect Separation of Concerns?
- Does it follow the Single Responsibility Principle?
- Are module responsibilities clearly maintained?
- Does it preserve stable module contracts?
- Does it respect ADRs?
- Does it avoid unnecessary coupling?
- Do dependencies point toward stable abstractions?
- Is business logic independent of infrastructure?
- Does the implementation preserve dependency direction?
- Does the implementation avoid database-specific logic outside the infrastructure layer?

---

# 3. Code Quality

- Is the code readable?
- Are variable names descriptive?
- Are function names meaningful?
- Is duplicate logic avoided?
- Is the implementation simple and maintainable?
- Is the code easy to test?
- Are abstractions preferred over conditional logic where appropriate?

---

# 4. Error Handling

- Are expected failures handled appropriately?
- Are exceptions meaningful?
- Are custom exceptions used where appropriate?
- Are transactions committed and rolled back correctly (where applicable)?

---

# 5. Logging

- Are important operations logged?
- Is the shared logger used?
- Is unnecessary logging avoided?
- Are error logs actionable without exposing sensitive information?

---

# 6. Configuration

- Are configuration values centralized?
- Are constants hardcoded?
- Does the implementation use shared configuration?
- Is environment/configuration independent from business logic?
- Are runtime settings used instead of hard-coded infrastructure values?

---

# 7. Testing

- Has smoke testing been completed?
- Have edge cases been considered?
- Have failure scenarios been considered?
- Infrastructure Validation (when applicable):
  - Database initialization verified?
  - Repository operations validated?
  - Cross-database compatibility considered?

---

# 8. Documentation

- Is documentation updated if required?
- Does the change require a new ADR?
- Are Architecture.md and Project Journal updated if necessary?
- Is README updated (if user-facing behavior changes)?
- Is PROJECT_STATE synchronized?
- Is CHANGELOG updated?
- Is the Sprint Release Report updated (if applicable)?

---

# 9. Git

- Is the commit history clean?
- Is the branch appropriately named?
- Are commit messages descriptive?

---

# Final Review

Before approving, ask:

- Would another engineer understand this code six months from now?
- Could this implementation be extended without modifying existing business modules?
- Does this implementation preserve existing public interfaces?
- Does this improve maintainability?
- Does this improve scalability?
- Would this pass an enterprise code review?

Only approve if the implementation meets the project's engineering standards.
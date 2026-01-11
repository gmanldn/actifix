# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the Actifix project. ADRs document important architectural decisions, their context, and their consequences.

## What are ADRs?

Architecture Decision Records are short text documents that capture an important architectural decision made along with its context and consequences. They help teams understand why certain decisions were made and provide historical context for future changes.

## ADR Format

Each ADR follows this structure:

```markdown
# ADR-XXXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-YYYY]

## Context
[What is the issue that we're seeing that is motivating this decision or change?]

## Decision
[What is the change that we're proposing and/or doing?]

## Consequences
[What becomes easier or more difficult to do because of this change?]

## Alternatives Considered
[What other options were considered and why were they rejected?]

## References
[Links to relevant documentation, discussions, or external resources]
```

## Naming Convention

ADRs are numbered sequentially and use descriptive titles:
- `ADR-0001-use-markdown-for-documentation.md`
- `ADR-0002-adopt-sqlite-for-persistence.md`
- `ADR-0003-implement-ai-provider-fallback.md`

## Current ADRs

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0001](ADR-0001-use-markdown-for-documentation.md) | Use Markdown for Documentation | Accepted | 2026-01-11 |
| [0002](ADR-0002-adopt-sqlite-for-persistence.md) | Adopt SQLite for Persistence | Accepted | 2026-01-11 |
| [0003](ADR-0003-implement-ai-provider-fallback.md) | Implement AI Provider Fallback | Accepted | 2026-01-11 |
| [0004](ADR-0004-enforce-raise-af-workflow.md) | Enforce Raise_AF Workflow | Accepted | 2026-01-11 |

## Creating New ADRs

1. **Identify the Decision**: Determine what architectural decision needs to be documented
2. **Assign Number**: Use the next sequential number
3. **Create File**: Use the naming convention above
4. **Fill Template**: Use the standard ADR format
5. **Review**: Have the decision reviewed by the team
6. **Update Index**: Add the new ADR to the table above

## Guidelines

- **Be Concise**: ADRs should be short and focused
- **Be Specific**: Include concrete details about the decision
- **Include Context**: Explain why the decision was necessary
- **Document Alternatives**: Show what other options were considered
- **Update Status**: Keep the status current as decisions evolve
- **Link Related ADRs**: Reference related decisions

## ADR Lifecycle

1. **Proposed**: Initial draft, under discussion
2. **Accepted**: Decision has been made and approved
3. **Deprecated**: Decision is no longer recommended
4. **Superseded**: Replaced by a newer ADR

## Tools

- **ADR Tools**: Consider using [adr-tools](https://github.com/npryce/adr-tools) for managing ADRs
- **Templates**: Use the template above for consistency
- **Reviews**: All ADRs should be reviewed before acceptance

## References

- [Architecture Decision Records](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR Template by Michael Nygard](https://github.com/joelparkerhenderson/architecture_decision_record/blob/master/adr_template_by_michael_nygard.md)

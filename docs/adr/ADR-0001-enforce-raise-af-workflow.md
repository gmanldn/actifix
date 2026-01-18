# ADR-0001: Enforce Raise_AF Workflow

## Status
Accepted

## Context

Actifix is designed as a self-improving error management framework that tracks its own development and improvements. To maintain consistency and ensure all changes are properly tracked, we need a mandatory workflow that requires all changes to start through the error capture system.

The challenge is ensuring that:
1. All development work is properly tracked and ticketed
2. Changes follow a consistent workflow
3. The system maintains its self-improving characteristics
4. AI agents and human developers follow the same process

Without a mandatory workflow, changes could bypass the tracking system, leading to:
- Untracked modifications
- Inconsistent development practices
- Loss of audit trail
- Reduced effectiveness of the self-improvement system

## Decision

We will enforce the Raise_AF workflow as a mandatory gate for all changes to the Actifix system:

1. **Environment Variable Gate**: Set `ACTIFIX_CHANGE_ORIGIN=raise_af` as a required environment variable
2. **Ticket Creation**: All work must begin by creating a ticket via `actifix.raise_af.record_error()`
3. **Workflow Enforcement**: The system will fail fast if changes are attempted without proper ticket creation
4. **Workflow**: Work directly on `develop` with regular pushes; no per-change branches required.
5. **Documentation**: All changes must be documented in tickets with proper context

The workflow steps are:
```bash
# 1. Set environment variable
export ACTIFIX_CHANGE_ORIGIN=raise_af

# 2. Create ticket via raise_af
python3 -c "from actifix.raise_af import record_error; record_error(...)"

# 3. Implement changes directly on develop
# ... development work ...

# 4. Test and commit
python3 test.py --coverage
git commit -m "feat(scope): description"

git push
```

## Consequences

### Positive
- **Consistent Tracking**: All changes are properly tracked and ticketed
- **Audit Trail**: Complete history of all modifications
- **Self-Improvement**: System maintains its self-tracking characteristics
- **Quality Gates**: Enforced testing and validation before changes
- **Documentation**: All work is documented with context and rationale

### Negative
- **Additional Overhead**: Requires extra steps for simple changes
- **Learning Curve**: Developers must learn the workflow
- **Potential Friction**: May slow down rapid prototyping
- **Emergency Bypass**: Need mechanism for critical emergency fixes

### Mitigations
- **Clear Documentation**: Comprehensive guides in AGENTS.md and DEVELOPMENT.md
- **Emergency Bypass**: `ACTIFIX_ENFORCE_RAISE_AF=0` for critical situations
- **Tooling**: Scripts and helpers to streamline the workflow
- **Training**: Clear examples and templates for common scenarios

## Alternatives Considered

### 1. Optional Workflow
**Rejected**: Would lead to inconsistent tracking and defeat the purpose of self-improvement

### 2. Post-Hoc Tracking
**Rejected**: Changes could be missed, and context would be lost

### 3. Git Hook Enforcement
**Rejected**: Too rigid and would prevent legitimate emergency fixes

### 4. Manual Process
**Rejected**: Prone to human error and inconsistent application

## References

- [AGENTS.md](../AGENTS.md) - Agent instructions and mandatory rules
- [DEVELOPMENT.md](../DEVELOPMENT.md) - Development workflow documentation
- [raise_af.py](../../src/actifix/raise_af.py) - Error capture implementation
- [Actifix Architecture](../architecture/ARCHITECTURE_CORE.md) - Core architectural principles

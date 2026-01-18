# Token Robustness Campaign

This document captures the scope and operating rules for token-robustness work: keeping AI payloads compact, predictable, and safe without losing critical context.

## Goals
- Keep AI payloads bounded and deterministic.
- Preserve critical context while trimming noise.
- Prevent runaway storage growth in tickets and logs.
- Maintain strict secret redaction and deduplication.

## Focus areas
1. **Raise_AF capture**
   - Enforce context limits for stack traces, file context, and system state.
   - Cache sanitized environment snapshots to reduce repeated payloads.
   - Track token deltas for AI remediation notes.

2. **DoAF dispatch**
   - Gate payload size before dispatch.
   - Split large remediation prompts into smaller, deterministic chunks.

3. **Persistence and queues**
   - Trim empty or redundant fields before enqueueing.
   - Ensure atomic writes remain bounded under load.

4. **AI providers**
   - Normalize prompt sizes across providers.
   - Keep fallback behavior deterministic under size pressure.

5. **Security and throttling**
   - Maintain secret redaction in cached payloads.
   - Enforce priority-aware throttling for floods.

## Working the campaign
- Use Raise_AF to create tickets for each scoped improvement.
- Capture evidence: before/after payload sizes and performance impact.
- Track progress in `data/actifix.db` rather than standalone plans.

Example query:
```bash
sqlite3 data/actifix.db "SELECT id, priority, status, message FROM tickets WHERE message LIKE '%token%' ORDER BY created_at DESC;"
```

## Success criteria
- Payload sizes remain within configured bounds.
- No regressions in capture fidelity or deduplication.
- Stable performance under burst ticket creation.

## References
- `docs/FRAMEWORK_OVERVIEW.md`
- `docs/DEVELOPMENT.md`
- `docs/INSTALLATION.md`

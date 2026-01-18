# Actifix QUICKDEV Guide

Focused guidance for AI agents and developers shipping Actifix modules quickly while staying compliant with the architecture map and Raise_AF workflow.

## What makes a module Actifix-ready
- **Single entrypoint** under `src/actifix/` (module or package).
- **Documented contract** in `docs/architecture/MAP.yaml` and `docs/architecture/MODULES.md`.
- **Central logging** via `actifix.log_utils.log_event` only.
- **Health visibility** through `actifix.health` or module-specific probes.
- **Error capture** through `actifix.raise_af.record_error` with re-raise.
- **Explicit dependencies** that respect the architecture graph.

## Fast path workflow
1. **Set the Raise_AF guard**
   ```bash
   export ACTIFIX_CHANGE_ORIGIN=raise_af
   ```
2. **Create module and tests**
   ```bash
   touch src/actifix/<module>.py
   touch test/test_<module>.py
   ```
3. **Wire logging and paths**
   ```python
   from actifix.log_utils import log_event
   from actifix.state_paths import get_actifix_paths
   from actifix.raise_af import record_error
   ```
4. **Update architecture docs**
   - `docs/architecture/MAP.yaml`
   - `docs/architecture/DEPGRAPH.json`
   - `docs/architecture/MODULES.md`
5. **Update docs**
   - Add notes to `docs/FRAMEWORK_OVERVIEW.md` if new behavior
   - Update `docs/INDEX.md` if sections move
6. **Test and ship**
   ```bash
   python3 test.py --coverage
   git commit -m "feat(<module>): add module entrypoint"
   git push
   ```

## Example skeleton
```python
from actifix.log_utils import log_event
from actifix.state_paths import get_actifix_paths
from actifix.raise_af import record_error


def bootstrap(project_root=None):
    paths = get_actifix_paths(project_root=project_root)
    log_event(paths.aflog_file, "MODULE_BOOTSTRAP", "module started")
    return paths


def run_task(paths):
    try:
        log_event(paths.aflog_file, "MODULE_TASK", "task started")
    except Exception as exc:
        record_error(
            message=str(exc),
            source="<module>.py:run_task",
            run_label="<module>",
            error_type=type(exc).__name__,
        )
        raise
```

## Simple ticket attack helper
Create a controlled backlog for automation experiments:
```bash
ACTIFIX_CHANGE_ORIGIN=raise_af ACTIFIX_CAPTURE_ENABLED=1 \
  python3 -m actifix.simple_ticket_attack --count 200
```

Options:
- `--count`: total tickets to create
- `--start-index`: offset numbering
- `--priority`: set P0-P3 for the batch
- `--run-label`: override run label
- `--capture-context`: include file/system context
- `--dry-run`: preview without writing

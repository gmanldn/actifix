# Version Synchronization Solution

## Problem
The UI version must always match the API version so the dashboard can detect mismatches, prompt a reload, and keep users confident that the backend and frontend are bundled from the same release. When the number drifted, the warning badge appeared and the tests flagged the discrepancy.

## Root Cause
Historically the version lived in several files:

1. `pyproject.toml` (the canonical source of truth)
2. `src/actifix/__init__.py` (a hardcoded `__version__`)
3. `actifix-frontend/app.js` (the `UI_VERSION` constant)

Releasing a new version meant updating each location manually, and it was easy to forget the frontend or docs.

## Solution

1. **Backend version resolution**  
   `src/actifix/__init__.py` now calls `_resolve_version()` to read the version straight from `pyproject.toml`. That means the API always exposes the canonical version, we do not hardcode `__version__`, and the `/api/version` endpoint is kept in sync automatically.

2. **Frontend synchronization**  
   `scripts/build_frontend.py` reads `pyproject.toml` via `get_version_from_pyproject()` and rewrites the `UI_VERSION` constant in `actifix-frontend/app.js`. The same version is also embedded in `actifix-frontend/index.html` via `ACTIFIX_ASSET_VERSION` so the served assets advertise the release number.

3. **Release flow**  
-   During a release, update `pyproject.toml` to the new number (e.g., `7.0.7`), run `python3 scripts/build_frontend.py`, and rebuild the `actifix-frontend` assets. The launcher (`scripts/start.py`) and tests (`test/test_version_synchronization.py`) then confirm all surfaces show the new version and highlight any mismatch.

## Usage

### Building the frontend

```bash
python3 scripts/build_frontend.py
```

This script:

- Extracts the version from `pyproject.toml`.
- Updates `actifix-frontend/app.js` (`UI_VERSION`) and `index.html` (`ACTIFIX_ASSET_VERSION`/query strings).
- Copies the updated files into `actifix-frontend/dist/`.

### Version display

- The React UI compares the API `/api/version` payload with the hardcoded `UI_VERSION`. When they match (as they should after the build script runs) the version badge shows `v7.0.7`; if not, the UI prompts a reload and records a warning to help catch release drift.

## Testing

- `python3 -m pytest test/test_version_synchronization.py` validates that `pyproject.toml`, the backend `__version__`, the API `/api/version`, and the frontend `UI_VERSION` all agree on the release string (currently `7.0.7`).
- The `@pytest.mark.slow` check in the same file ensures no legacy `5.x` numbers remain in the production files so future builds start clean.

Keeping this doc up to date with every release ensures the release gate stays green and the frontend never drifts from the backend version.

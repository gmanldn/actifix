# Version Synchronization Solution

## Problem
The UI version didn't match the API version. They should always be the same - a single project version at any time.

## Root Cause
The versions were defined in three separate files and were not synchronized:

1. **Backend** (`src/actifix/__init__.py`): `__version__ = "5.0.0"` (outdated)
2. **Frontend** (`actifix-frontend/app.js`): `UI_VERSION = '5.0.50'`
3. **pyproject.toml**: `version = "5.0.50"` (canonical source)

## Solution

### 1. Updated Backend Version
Changed `src/actifix/__init__.py` to use the canonical version from `pyproject.toml`:
```python
__version__ = "5.0.50"  # Now matches pyproject.toml
```

### 2. Enhanced Build Script
Updated `scripts/build_frontend.py` to automatically sync the frontend version from `pyproject.toml` during the build process:

- Added `_get_version_from_pyproject()` function to extract version from `pyproject.toml`
- Added `_update_frontend_version()` function to update `UI_VERSION` in `app.js`
- The build script now:
  1. Reads the version from `pyproject.toml` (single source of truth)
  2. Updates the frontend `UI_VERSION` to match
  3. Copies files to the dist directory

### 3. Version Flow
```
pyproject.toml (source of truth)
       ↓
   build_frontend.py
       ↓
   actifix-frontend/app.js (UI_VERSION synced)
       ↓
   src/actifix/__init__.py (__version__ matches)
       ↓
   API /version endpoint returns correct version
```

## Usage

### Building the Frontend
```bash
python3 scripts/build_frontend.py
```

This will:
- Extract version from `pyproject.toml`
- Update `actifix-frontend/app.js` with the correct `UI_VERSION`
- Copy files to `actifix-frontend/dist/`

### Version Display
The frontend displays the version in the header via the `VersionBadge` component, which:
1. Fetches version from `/api/version` endpoint
2. Compares it with the hardcoded `UI_VERSION`
3. Shows a warning if they don't match
4. Auto-reloads the page if a version change is detected

## Benefits
- **Single source of truth**: Version is only defined in `pyproject.toml`
- **Automatic synchronization**: Build script ensures frontend version matches
- **No manual updates needed**: Version updates automatically when `pyproject.toml` changes
- **Consistent versioning**: UI and API always show the same version

## Testing
All three versions are now synchronized at `5.0.50`:
- Frontend `UI_VERSION`: 5.0.50
- Backend `__version__`: 5.0.50
- `pyproject.toml`: 5.0.50
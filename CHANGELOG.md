# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

## [7.0.4] - 2026-01-29

### Added
- Reinforced the AGENTS workflow so every agent must read the README, AGENTS, and `docs/INDEX.md` before touching the code, ensuring Actifix rules are obeyed before tasks begin.

### Changed
- Updated `AGENTS.md` to insist on obeying the Actifix rules and on reading the core documentation prior to work, with the release history/table now noting the strengthened guardrails.

### Fixed
- None (boilerplate release for workflow enforcement).

## [7.0.2] - 2026-01-28

### Added
- The launcher now aggressively terminates stray Actifix-related processes (including `python` and `start.py` sessions) and cleans both `.pyc` files and `__pycache__` directories before any new startup, ensuring no old code is still running.

### Changed
- `cleanup_existing_instances()` now scans for lingering Actifix commands and escalates termination, while the bytecode cache cleanup also purges `__pycache__` folders so the fresh start uses rebuilt artifacts.

### Fixed
- Startup scripts no longer leave behind ghosts on the runtime ports or stale bytecode from previous launches, so every run begins from a clean slate.

## [7.0.1] - 2026-01-27

### Added
- Minor release notes that capture the patched synchronization flow and release guidance so the timeline reflects the 7.0.y cadence.

### Changed
- Canonical version metadata, frontend assets, and documentation pointers now show 7.0.1 so release tooling stays in sync across both branches.

### Fixed
- Cleared stale release references and ensured the version sync documentation mentions the latest patch release number, keeping the audit-heavy tests green.

## [7.0.0] - 2026-01-26

### Added
- Release documentation now calls out the 7.0.0 big-point release so the timeline and highlights stay discoverable in `docs/FRAMEWORK_OVERVIEW`.

### Changed
- Bumped the canonical version to 7.0.0 and synchronized the frontend asset, version badge, and API surfaces with the new number.
- Updated the version synchronization guidance and `docs/INDEX` pointers so the release flow clarifies the single source of truth.

### Fixed
- Removed stale 5.x version references from production docs so the version audit tests run cleanly against the latest release.

## [6.0.31] - 2026-01-25

### Added
- Ticket filter bar (priority/status/search) so dashboard lanes can be scoped client-side
- Log summary grid + severity chips with updated metadata and helper tokens in the compact log view

### Changed
- Frontend UI_VERSION aligned with backend (6.0.31) and assets rebuilt

## [6.0.25] - 2026-01-25

### Added
- Tests covering background DoAF agent fallback completion and AgentVoice logging

## [6.0.24] - 2026-01-25

### Added
- Launcher support for running the DoAF background ticket agent alongside services

### Changed
- Daemon documentation now covers running the ticket agent via launchctl

## [6.0.23] - 2026-01-25

### Added
- DoAF agent heartbeat tracking written to state and surfaced in health reports

### Changed
- Health report includes DoAF agent liveness details and warns on stale heartbeats

## [6.0.22] - 2026-01-25

### Added
- Non-interactive fallback completion for background DoAF processing via `--fallback-complete`

### Changed
- Background DoAF agent CLI now exposes explicit fallback behavior controls

## [6.0.21] - 2026-01-25

### Added
- 50 actionable tasks implementation from documentation analysis
- Comprehensive task list with priority distribution
- Initial ticket creation via raise_af workflow
- Launcher now starts the standalone PokerTool service by default (use `--pokertool-port` / `--no-pokertool`) and records a `POKERTOOL_SERVICE_START` event so the new module shows up with the other GUIs.
- Background DoAF agent loop with lease renewal, idle backoff, and a dedicated CLI command
- AgentVoice logging for DoAF dispatch lifecycle events

### Changed
- Move the consolidated test runner into `test/test_runner.py` and align the docs/architecture references with the new path
- Refresh the dashboard ticket feed more frequently and group tickets by priority lanes in the UI
- Stop tracking local `data/actifix.db` artifacts in git and ignore the runtime SQLite WAL files
- Ensure bootstrap initializes the ticket database and add root symlink guards for start/test helpers
- Consolidate and refresh documentation across quickstart, installation, development, and testing guides
- AI client now honors the configured Claude API model for Anthropic calls
- Modules API now includes runtime host/port metadata, and the UI exposes a refresh control with port display

### Fixed
- Automatically tighten `data/actifix.db` permissions to `chmod 600` before validation so the world-readable guard rails only flag intentionally insecure paths.

## [2.7.0] - 2026-01-11

### Added
- Multi-provider AI integration with automatic fallback chain
- Claude Code local auth detection
- Claude API integration
- OpenAI GPT-4 Turbo integration
- Ollama local model support
- Free alternative user prompts
- Automatic provider fallback
- Cost tracking and logging
- SQLite database backend with connection pooling
- Ticket repository with CRUD operations and locking
- Database migration script for importing tickets
- Enhanced persistence layer with atomic operations
- Comprehensive testing framework
- Architecture compliance validation
- Health monitoring system
- Quarantine system for error isolation

### Changed
- Improved error capture with rich context
- Enhanced ticket processing workflow
- Better AI remediation notes generation
- Optimized state management
- Refined architecture documentation

### Fixed
- Thread safety issues in database operations
- Memory leaks in long-running processes
- Error handling edge cases
- Configuration validation bugs

## [2.6.0] - 2026-01-10

### Added
- Self-improving error management framework
- Production-grade error capture with priority classification
- AI-native ticket generation
- Self-development mode for framework improvement
- Transparent Markdown artifacts
- Configurable environment variables
- Web dashboard frontend
- Comprehensive documentation suite

### Changed
- Refactored core architecture for better modularity
- Improved error classification algorithm
- Enhanced duplicate detection mechanism
- Better secret redaction capabilities

### Fixed
- Race conditions in concurrent error capture
- File corruption issues during atomic writes
- Memory usage optimization
- Performance bottlenecks in ticket processing

## [2.5.0] - 2026-01-09

### Added
- Initial framework implementation
- Basic error capture and ticket creation
- Simple file-based persistence
- Command-line interface
- Basic testing infrastructure

### Changed
- Initial architecture design
- Core module structure
- Basic configuration system

## [2.0.0] - 2026-01-01

### Added
- Project inception
- Core concept development
- Initial design documents

---

## Release Notes

### Version 2.7.0 Highlights
This release focuses on AI integration and database persistence, making Actifix production-ready with multi-provider AI support and robust data storage.

### Version 2.6.0 Highlights
Major milestone introducing the self-improving error management framework with comprehensive documentation and web interface.

### Version 2.5.0 Highlights
Foundation release establishing core error capture and ticket management capabilities.

## Migration Guide

### Upgrading to 2.7.0
- Tickets are now stored exclusively in `data/actifix.db`; existing Markdown archives are ignored and no manual migration is required because the database is already authoritative
- Update configuration for AI provider settings
- Review new environment variables for AI integration

### Upgrading to 2.6.0
- No breaking changes from 2.5.0
- New configuration options available
- Web dashboard requires static file serving

## Support

For questions about releases or upgrade issues:
- Check the documentation in `docs/`
- Review architecture files in `docs/architecture/`
- Report issues via GitHub Issues
- See `docs/DEVELOPMENT.md` for contribution guidelines

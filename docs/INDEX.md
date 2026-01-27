# Actifix Documentation Index

This index keeps documentation discoverable and aligned with the Actifix workflow. Start here, then follow the guides that match your role.

## Start here
- **README** `../README.md` - project overview, core commands, guardrails
- **QUICKSTART** `QUICKSTART.md` - fastest path to running Actifix
- **INSTALLATION** `INSTALLATION.md` - installation and configuration details
- **FRAMEWORK OVERVIEW** [`FRAMEWORK_OVERVIEW.md#dashboard-panes`](FRAMEWORK_OVERVIEW.md#dashboard-panes) - architecture, dashboard panes (incl. new Ideas pane), release notes, roadmap
- **RELEASE NOTES** [`FRAMEWORK_OVERVIEW.md#release-notes-and-version-history`](FRAMEWORK_OVERVIEW.md#release-notes-and-version-history) - version history and highlights featuring the 7.0.7 release
- **BACKGROUND TICKET AGENT** `FRAMEWORK_OVERVIEW.md#background-ticket-agent` - background DoAF loop usage and behavior
- **BACKGROUND TICKET AGENT ROADMAP** `FRAMEWORK_OVERVIEW.md#background-ticket-agent-roadmap` - readiness gaps and tracked tickets for background processing
- **MODULE CONFIGURATION** `FRAMEWORK_OVERVIEW.md#module-configuration` - module defaults and override schema
- **MODULE METADATA + HEALTH** `FRAMEWORK_OVERVIEW.md#module-metadata-and-permissions` - module metadata schema and health aggregation.
- **MODULE LIFECYCLE** `FRAMEWORK_OVERVIEW.md#module-lifecycle-and-helpers` - ModuleBase helpers, ModuleRegistry discovery, and status persistence.
- **AGENTVOICE (AGENTTHOUGHTS)** `FRAMEWORK_OVERVIEW.md#agentvoice-agentthoughts-review-log` - module info/error review stream in `data/actifix.db`.
- **GITHUB ISSUE SYNC** `FRAMEWORK_OVERVIEW.md#github-issue-sync` - instructions for publishing tickets to GitHub and tracking the resulting issue metadata.

## Operators and support
- **MONITORING** `MONITORING.md` - health checks, metrics, and alerting
- **TROUBLESHOOTING** `TROUBLESHOOTING.md` - common issues and fixes
- **ADMIN AUTHENTICATION** `ADMIN_AUTHENTICATION.md` - admin user setup, password management, and authentication
- **QUICK ADMIN SETUP** `QUICK_ADMIN_SETUP.md` - quick reference for admin authentication
- **IMPLEMENTATION SUMMARY** `IMPLEMENTATION_SUMMARY.md` - admin authentication implementation details
- **VERSION SYNC SOLUTION** `VERSION_SYNC_SOLUTION.md` - UI/API version synchronization and build process

## Development and testing
- **DEVELOPMENT GUIDE** `DEVELOPMENT.md` - workflow, quality gates, ticket completion
- **QUICKDEV** `QUICKDEV.md` - fast module-building workflow
- **TESTING** `TESTING.md` - test runner, quality gates, and coverage
  - **TEST PERFORMANCE** `TEST_PERFORMANCE_OPTIMIZATION.md` - speed, timeouts, and profiling
  - **DOCTOR COMMAND** `DEVELOPMENT.md#doctor-command` - diagnose environment and configuration
- **TEST MARKERS** `TEST_MARKERS_GUIDE.md` - marker taxonomy and usage
- **COVERAGE OPTIMIZATION** `COVERAGE_OPTIMIZATION.md` - fast coverage workflow
- **ADR directory** `adr/` - architecture decisions (Raise_AF workflow)

## Architecture references
- **ARCHITECTURE CORE** `architecture/ARCHITECTURE_CORE.md`
- **MODULES** `architecture/MODULES.md`
- **MAP** `architecture/MAP.yaml`
- **DEPGRAPH** `architecture/DEPGRAPH.json`

## Campaigns and initiatives
- **TOKEN ROBUSTNESS CAMPAIGN** `token_robustness_campaign.md`
- **ULTRATHINK TICKETS SUMMARY** `ultrathink_tickets_summary.md`

## Legal
- **LICENSE** `legal/LICENSE.md`

## Document status
| Document | Status | Notes |
|----------|--------|-------|
| README | Updated | Overview and commands aligned to current CLI. |
| QUICKSTART | Updated | Hands-on setup and first ticket. |
| INSTALLATION | Updated | Environment and dependency setup. |
| FRAMEWORK_OVERVIEW | Updated | Architecture overview plus release notes now covering the 7.0.7 release. |
| DEVELOPMENT | Updated | Raise_AF workflow and quality gates. |
| ARCHITECTURE MAP/GRAPH | Auto-generated | Source of truth for module graph. |
| TESTING | Updated | Test runner and markers aligned to repo. |
| MONITORING | Updated | Operational guidance and queries. |
| TROUBLESHOOTING | Updated | Common issues aligned to actual commands. |
| VERSION_SYNC_SOLUTION | Updated | Version synchronization guidance refreshed for the current release and canonical pyproject flow. |

_Last updated: 2026-01-29_

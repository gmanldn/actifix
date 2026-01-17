# Actifix Documentation Index

This index keeps all documentation concise, cross-referenced, and aligned with the Actifix workflow. Start here, then follow the links that fit your role.

## Quick access
- **README** [../README.md](../README.md) – Project overview (capture, self-improvement, commands).
- **QUICKSTART** [QUICKSTART.md](QUICKSTART.md) – Hands-on setup plus capture + ticket inspection snippets.
- **INSTALLATION** [INSTALLATION.md](INSTALLATION.md) – Platform-specific install and environment variables.
- **FRAMEWORK OVERVIEW** [FRAMEWORK_OVERVIEW.md](FRAMEWORK_OVERVIEW.md) – Purpose, architecture, release notes, and roadmap.

## User & operator guides
- **MONITORING** [MONITORING.md](MONITORING.md) – Operational metrics, health checks, alerting patterns.
- **TROUBLESHOOTING** [TROUBLESHOOTING.md](TROUBLESHOOTING.md) – Frequently seen issues with rapid remedies.
- **TESTING** [TESTING.md](TESTING.md) – Testing philosophy and quality gate descriptions.
- **TEST PERFORMANCE** [TEST_PERFORMANCE_OPTIMIZATION.md](TEST_PERFORMANCE_OPTIMIZATION.md) – Running fast, stable test suites.
- **TEST MARKERS** [TEST_MARKERS_GUIDE.md](TEST_MARKERS_GUIDE.md) – Marker-based test selection guidelines.
- **COVERAGE OPTIMIZATION** [COVERAGE_OPTIMIZATION.md](COVERAGE_OPTIMIZATION.md) and [notes/COVERAGE_OPTIMIZATION_SUMMARY.md](notes/COVERAGE_OPTIMIZATION_SUMMARY.md) – Improving coverage while keeping runs fast.

## Developer & architecture resources
- **DEVELOPMENT GUIDE** [DEVELOPMENT.md](DEVELOPMENT.md) – Workflow, QA gates, architecture validation, and doc standards.
- **QUICKDEV** [QUICKDEV.md](QUICKDEV.md) – Focused workflows for agent-powered development sprints.
- **ADR directory** [adr/](adr/) – Raised AF workflow and future architecture decisions.
- **Architecture docs** – [ARCHITECTURE_CORE.md](architecture/ARCHITECTURE_CORE.md), [MODULES.md](architecture/MODULES.md), [MAP.yaml](architecture/MAP.yaml), [DEPGRAPH.json](architecture/DEPGRAPH.json) describe the canonical topology. Update everything when the module map changes.
- **Notes** [notes/](notes/) – Summaries, debugging reports, and documentation planning (use only for reference).

## Self-improvement & automation
- **Token robustness campaign** [token_robustness_campaign.md](token_robustness_campaign.md) – Ongoing AI/robustness experiments.
- **Ultrathink ticket summaries** [ultrathink_tickets_summary.md](ultrathink_tickets_summary.md) – Elevator notes from the most complex ticket bursts.
- **Automation folder** [automation/](automation/) – Scripts that spawn mass-ticket workflows and diagnostics.

## Legal & compliance
- **LICENSE** [legal/LICENSE.md](legal/LICENSE.md)

## Document status
| Document | Status | Notes |
|----------|--------|-------|
| README | ✅ Updated 2026-01-17 | Landing overview for all audiences.
| QUICKSTART | ✅ Updated 2026-01-17 | Hands-on install + capture.
| FRAMEWORK_OVERVIEW | ✅ Updated 2026-01-17 | Architecture, release notes, roadmap.
| DEVELOPMENT | ✅ Updated 2026-01-17 | Workflow, QA gates, architecture, docs.
| ARCHITECTURE MAP/GRAPH | ✅ Auto-generated weekly | Source of truth for module graph.
| TROUBLESHOOTING | 🚧 Conditional updates | Scoped fixes referenced in releases.
| MONITORING | 🚧 Conditional updates | Refer to release notes for telemetry.
| TESTING & OPTIMIZATION | ✅ Coverage guidelines in place | Balanced tests and performance tips.

## How to contribute docs
1. Update the relevant document directly in the `docs/` folder.
2. Sync `docs/INDEX.md` to include any new section.
3. Link to architecture artifacts when structural changes occur.
4. Release notes always live in the “Release Notes & Version History” section of `docs/FRAMEWORK_OVERVIEW.md`.

_Last updated: 2026-01-17_
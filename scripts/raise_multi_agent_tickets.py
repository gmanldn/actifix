#!/usr/bin/env python3
"""
Raise actifix tickets to prepare codebase for multiple AI agents working in tandem.
Ensures database and binary data remain untracked to prevent merge conflicts.
"""
import sys
sys.path.insert(0, 'src')

from actifix.bootstrap import ActifixContext
from actifix.raise_af import record_error, TicketPriority

with ActifixContext():
    # Ticket 1: P1 - Update .gitignore to exclude database files
    record_error(
        message=".gitignore must exclude data/actifix.db and all binary data to prevent merge conflicts. Database must remain untracked so multiple AI agents can work without corrupting each other's state.",
        source="AGENTS.md:1",
        error_type="Feature",
        priority=TicketPriority.P1,
        run_label="multi_agent_preparation",
        ai_remediation_notes="Ensure .gitignore includes: data/actifix.db, data/actifix.db-shm, data/actifix.db-wal, and any other binary data. Update documentation to explain why database is untracked.",
    )
    
    # Ticket 2: P1 - CI/CD checks to prevent binary data commits
    record_error(
        message="Implement CI/CD pre-commit hooks and GitHub Actions checks to reject commits containing binary data files (databases, images, compiled artifacts). This is critical for multi-agent workflow where multiple agents may modify the same repository simultaneously.",
        source="AGENTS.md:1",
        error_type="Feature",
        priority=TicketPriority.P1,
        run_label="multi_agent_preparation",
        ai_remediation_notes="Create pre-commit hook in scripts/pre-commit-hook.py that scans for binary file extensions and prevents their commit. Add GitHub Actions workflow to validate commits don't contain binary data.",
    )
    
    # Ticket 3: P2 - Document multi-agent workflow in docs/FRAMEWORK_OVERVIEW.md
    record_error(
        message="Document the multi-agent workflow where multiple AI agents work on develop branch simultaneously. Document that database remains untracked, agents create their own branches, and changes merge up into develop. Include branch naming conventions and merge strategies.",
        source="docs/FRAMEWORK_OVERVIEW.md",
        error_type="Docs",
        priority=TicketPriority.P2,
        run_label="multi_agent_preparation",
        ai_remediation_notes="Update docs/FRAMEWORK_OVERVIEW.md with a new section 'Multi-Agent Workflow' covering: 1) Why database is untracked, 2) Branch naming conventions (e.g., agent/feature-name), 3) Merge strategy (squash merge into develop), 4) Conflict resolution procedures.",
    )
    
    # Ticket 4: P2 - Create agent configuration templates
    record_error(
        message="Create configuration templates and scripts for setting up multiple AI agents. Each agent needs isolated configuration to prevent conflicts when working simultaneously on the same repository.",
        source="docs/DEVELOPMENT.md",
        error_type="Feature",
        priority=TicketPriority.P2,
        run_label="multi_agent_preparation",
        ai_remediation_notes="Create agent-config-template.sh and agent-setup.md in docs/. Provide example configurations for different agent types (e.g., agent-alpha, agent-beta) with separate environment variables and working directories.",
    )
    
    # Ticket 5: P3 - Add tests for multi-agent workflow
    record_error(
        message="Add integration tests to verify multi-agent workflow compatibility: 1) Database remains untracked in git status, 2) Multiple agents can create branches without conflicts, 3) Binary data files are properly excluded from version control.",
        source="test/test_multi_agent_workflow.py",
        error_type="Test",
        priority=TicketPriority.P3,
        run_label="multi_agent_preparation",
        ai_remediation_notes="Create test file test/test_multi_agent_workflow.py with tests that: 1) Verify .gitignore entries, 2) Simulate concurrent branch creation, 3) Test binary file detection in pre-commit hooks.",
    )
    
    # Ticket 6: P2 - Update README with multi-agent section
    record_error(
        message="Update README.md to include section on multi-agent workflow. Explain how multiple AI agents can work in tandem, why database is untracked, and provide quick-start guide for agent setup.",
        source="README.md",
        error_type="Docs",
        priority=TicketPriority.P2,
        run_label="multi_agent_preparation",
        ai_remediation_notes="Add 'Multi-Agent Workflow' section to README.md after 'Quickstart'. Include: 1) Overview of multi-agent capability, 2) Key principle (database untracked), 3) Quick agent setup steps, 4) Link to detailed docs.",
    )
    
    print("Successfully raised 6 actifix tickets for multi-agent workflow preparation:")
    print("- P1: Update .gitignore to exclude database files")
    print("- P1: Implement CI/CD checks to prevent binary data commits")
    print("- P2: Document multi-agent workflow in docs/FRAMEWORK_OVERVIEW.md")
    print("- P2: Create agent configuration templates")
    print("- P3: Add tests for multi-agent workflow")
    print("- P2: Update README with multi-agent section")
    print("\nTickets have been recorded in data/actifix.db and are ready for processing.")
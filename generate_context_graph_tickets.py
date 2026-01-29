#!/usr/bin/env python3
"""
generate_context_graph_tickets.py
=================================

This helper script creates a series of high‑value tickets that implement a
more sophisticated context memory system and richer architecture mapping for
the Actifix project.  The current ticketing system persists everything in
SQLite (see `database.py` for the existing ACID‑compliant backend【570742712764514†L4-L9】).  The
existing architecture map (`MAP.yaml`) is auto‑generated and serves as the
single source of truth for module ownership and dependencies【455750700079513†L7-L12】.  These
tickets extend both areas:

* A **context embeddings store** for long‑term project memory, implemented in
  SQLite and exposed through repository classes.
* A **conversation memory** table to maintain high‑context history across
  multiple agents and sessions.
* A **hierarchical project map** (repo_map/module_summary/symbol_index) to
  reduce token usage by fetching summaries before full code.
* An extended **architecture generator** that records complexity metrics,
  cross‑domain dependencies and edge types in `MAP.yaml` and `DEPGRAPH.json`.
* A set of tests, API endpoints and validation tooling to wire these pieces
  into the existing Actifix workflow.

When run, this script uses `record_error` from `actifix.raise_af` to create
tickets in the canonical SQLite database.  It also updates the
`ai_remediation_notes` field with detailed implementation guidance.  The
resulting tickets appear in `data/actifix.db` and can be processed via the
normal Actifix self‑repair workflows.
"""

from __future__ import annotations

import os
import sys

# Ensure we record tickets through the raise_af pipeline rather than
# alternative channels.  This environment variable tags the origin of the
# changes.
os.environ.setdefault("ACTIFIX_CHANGE_ORIGIN", "raise_af")

# Add the src directory to sys.path so that we can import internal modules.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from actifix.raise_af import record_error, TicketPriority
from actifix.persistence.ticket_repo import get_ticket_repository


# Each element in this list defines one ticket.  The tuple fields are:
# (message, source, error_type, priority, ai_notes)
#
# message:     A short summary of the ticket; this becomes the ticket title.
# source:      A file path and approximate line number suggesting where the
#              work will occur.  This helps maintainers locate the context.
# error_type:  A high‑level category (Feature, Refactor, Docs, Test, Quality).
# priority:    One of P0–P4 according to Actifix convention (P0 highest).
# ai_notes:    A detailed description of what needs to be done, including
#              suggested schema changes, function signatures, acceptance
#              criteria, and any design rationale.
TICKETS = [
    (
        "Create context_embeddings persistence and repository",
        "src/actifix/persistence/context_embeddings.py:1",
        "Feature",
        "P2",
        (
            "Introduce a new persistence module `context_embeddings.py` to store vector "
            "embeddings and associated metadata.  Define a SQLite table "
            "`context_embeddings` with columns:\n"
            "  - id INTEGER PRIMARY KEY AUTOINCREMENT\n"
            "  - doc_type TEXT NOT NULL (e.g. 'code', 'doc', 'summary')\n"
            "  - key TEXT NOT NULL (file path, module id or symbol name)\n"
            "  - chunk_index INTEGER NOT NULL (0‑based order of the chunk)\n"
            "  - vector BLOB NOT NULL (embedding bytes, use array.array or pickle)\n"
            "  - content TEXT NOT NULL (the plain text chunk)\n"
            "  - metadata TEXT (JSON‑encoded extra fields such as content_hash, commit)\n"
            "  - embedding_version INTEGER NOT NULL DEFAULT 1\n"
            "Add a UNIQUE constraint on (doc_type, key, chunk_index) and indexes on\n"
            "doc_type, key and embedding_version for efficient lookup.  Expose a "
            "dataclass `ContextEmbedding` and a repository class `ContextEmbeddingRepo` "
            "with methods: `add_embedding(doc_type, key, chunks, metadata)`, "
            "`update_embeddings(key, doc_type, chunks, metadata)`, and "
            "`get_embeddings(key, doc_type)` returning the ordered list of "
            "embeddings.  Migrate the database schema by extending "
            "`database.py` (SCHEMA_SQL and migration code) to create this new "
            "table.  Ensure WAL mode and existing concurrency semantics are "
            "maintained."
        ),
    ),
    (
        "Implement conversation_memory persistence for multi‑session history",
        "src/actifix/persistence/conversation_memory.py:1",
        "Feature",
        "P2",
        (
            "Add a new module `conversation_memory.py` that defines a table "
            "`conversation_memory` for persisting multi‑agent, multi‑session chat "
            "history.  The schema should include:\n"
            "  - id INTEGER PRIMARY KEY AUTOINCREMENT\n"
            "  - thread_id TEXT NOT NULL (global conversation identifier)\n"
            "  - session_id TEXT NOT NULL (session identifier per agent run)\n"
            "  - turn_index INTEGER NOT NULL (order within the session)\n"
            "  - speaker TEXT NOT NULL (e.g. 'user', 'assistant', 'tool')\n"
            "  - message TEXT NOT NULL (raw message content)\n"
            "  - metadata TEXT (JSON extra fields: timestamp, role, tool info)\n"
            "Create indexes on (thread_id, session_id, turn_index) and (thread_id, turn_index) "
            "to support chronological retrieval across sessions.  Provide a "
            "repository class `ConversationMemoryRepo` with methods: "
            "`append_turn(thread_id, session_id, speaker, message, metadata)` and "
            "`fetch_history(thread_id, limit=None, reverse=False)` returning an "
            "ordered list of turns.  Update migrations in `database.py` to "
            "create this table.  This enables high context retention across "
            "multiple agents and sessions."
        ),
    ),
    (
        "Add embeddings ingestion pipeline with Git diff detection",
        "src/actifix/ingestion.py:1",
        "Feature",
        "P2",
        (
            "Extend the existing ingestion system to compute and persist "
            "embeddings for source files and documentation.  Create functions "
            "`collect_repository_files()` and `chunk_and_embed()` that walk the "
            "project tree, break large files into token‑friendly chunks and "
            "obtain embeddings via the configured AI provider or local model.\n"
            "Detect changed files by comparing content hashes or using the Git "
            "diff API; only re‑embed files whose content has changed.  For each "
            "chunk, write a row into `context_embeddings` with metadata "
            "including the content_hash, file_path, commit_id and timestamp. "
            "Provide a CLI entry point or scheduled job to run this ingestion "
            "pipeline on demand.  Update existing ingestion tests to cover the "
            "embedding workflow."
        ),
    ),
    (
        "Provide similarity search and retrieval APIs for context embeddings",
        "src/actifix/persistence/context_embeddings.py:150",
        "Feature",
        "P2",
        (
            "Augment `ContextEmbeddingRepo` with vector similarity search.  Add "
            "a method `search_similar(query_vector, doc_type=None, top_k=5, filters=None)` "
            "that returns the top_k most similar chunks by cosine similarity.  If "
            "available, use efficient approximate nearest neighbour libraries "
            "(e.g. faiss or annoy) or compute dot products in Python for small "
            "datasets.  Apply optional filters on doc_type or key.  Expose the "
            "search through an API endpoint (see below) and return both the "
            "matching content and associated metadata.  Document the expected "
            "embedding length and ensure out‑of‑band errors propagate via "
            "`raise_af`."
        ),
    ),
    (
        "Build hierarchical project memory maps (repo_map, module_summary, symbol_index)",
        "src/actifix/persistence/repo_map.py:1",
        "Feature",
        "P3",
        (
            "Introduce a hierarchical memory layer to minimise token usage during "
            "retrieval.  Create a new persistence module `repo_map.py` that "
            "defines three tables: `repo_map` (path TEXT PRIMARY KEY, "
            "is_dir BOOLEAN, parent_path TEXT, summary TEXT), `module_summary` "
            "(module_id TEXT PRIMARY KEY, summary TEXT, details TEXT), and "
            "`symbol_index` (symbol_name TEXT PRIMARY KEY, file_path TEXT, "
            "start_line INTEGER, end_line INTEGER, summary TEXT).\n"
            "Implement a builder function that walks the codebase, summarises "
            "each directory and file into concise descriptions (e.g. using "
            "docstrings or heuristics), extracts function and class symbols via "
            "the AST and stores them in `symbol_index`.  Provide retrieval "
            "functions such as `get_repo_map()`, `get_module_summary(module_id)`, "
            "and `search_symbols(query)`.  Use these maps as a first stop "
            "before pulling raw code into prompts."
        ),
    ),
    (
        "Extend MAP.yaml generator with metrics and cross‑domain dependencies",
        "scripts/update_architecture_docs.py:1",
        "Refactor",
        "P3",
        (
            "Modify the architecture documentation generator to compute "
            "additional metrics for each module: number of functions, classes and "
            "lines of code; number of dependencies and domain cross‑overs; "
            "whether it touches persistence or security; and the number of "
            "public API entry points.  Embed these metrics into `MAP.yaml` under "
            "each module entry (e.g. metrics: {loc: 123, functions: 10, deps: 4}).\n"
            "Analyse import statements to classify dependency types (call, "
            "data_flow, event, plugin) and record them in the YAML.  Update the "
            "generator so that it continues to run automatically (per the meta "
            "notes) and document any new fields in the README."
        ),
    ),
    (
        "Generate extended DEPGRAPH with edge types and node metrics",
        "scripts/update_depgraph.py:1",
        "Feature",
        "P3",
        (
            "Create a new script `update_depgraph.py` that produces an "
            "enriched `DEPGRAPH.json`.  Each node should carry the metrics "
            "computed by the MAP.yaml generator (loc, functions, deps, domain, "
            "owner), and each edge should include a type (call, data_flow, "
            "event, plugin) and a weight (number of references).\n"
            "Provide a helper to export the graph in formats consumable by "
            "Graphviz or Mermaid for visualisation.  Update documentation to "
            "reference the new graph format."
        ),
    ),
    (
        "Add CLI command to regenerate architecture",
        "src/actifix/cli_framework.py:200",
        "Feature",
        "P3",
        (
            "Extend the CLI framework to include a `regenerate-architecture` command "
            "that invokes the updated architecture generator and DEPGRAPH scripts. "
            "The command should accept flags such as `--extended` (to compute "
            "metrics and edge types) and `--output-dir` for specifying where "
            "generated files should be written.  Integrate this command into "
            "`src/actifix/main.py` so that it appears in the top level CLI. "
            "Ensure that the CLI uses the existing logging system and exits "
            "with informative messages."
        ),
    ),
    (
        "Update architecture documentation for new context memory and graph model",
        "docs/architecture/ARCHITECTURE_CORE.md:1",
        "Docs",
        "P3",
        (
            "Revise the architecture documentation to explain the new context "
            "memory and architecture components.  Add sections describing the "
            "purpose and schema of `context_embeddings` and `conversation_memory`, "
            "along with examples of how embeddings and conversation history are "
            "queried and used by agents.  Provide an overview of the "
            "hierarchical project map and how it reduces token consumption.\n"
            "Document the extended `MAP.yaml` and `DEPGRAPH.json` formats, "
            "including the meaning of new fields and how to regenerate them. "
            "Update any diagrams or references to reflect the richer graph "
            "representation."
        ),
    ),
    (
        "Add tests for context_embeddings and conversation_memory persistence",
        "test/test_context_memory.py:1",
        "Test",
        "P2",
        (
            "Create a new test module `test_context_memory.py` that exercises "
            "the persistence layers introduced here.  Write tests for: "
            "inserting and retrieving embeddings; enforcing UNIQUE constraints; "
            "searching for similar chunks; verifying that conversation turns are "
            "stored and retrieved in order; handling multiple sessions per "
            "thread; and ensuring that migrations do not corrupt existing data.\n"
            "Include concurrency tests where multiple threads insert into "
            "`context_embeddings` and `conversation_memory` simultaneously, "
            "leveraging the WAL mode and connection pooling already present in "
            "`database.py`.  Ensure tests pass on SQLite and are marked "
            "appropriately for xdist or isolation."
        ),
    ),
    (
        "Implement architecture validator to ensure MAP.yaml matches code imports",
        "src/actifix/validators/architecture_validator.py:1",
        "Quality",
        "P2",
        (
            "Develop a validation module that compares the generated `MAP.yaml` "
            "against actual Python imports.  It should parse all modules under "
            "`src/actifix`, build an import graph, and check that every "
            "imported module appears in the map and that all declared "
            "dependencies are valid.  If discrepancies are found, the validator "
            "should either raise a `ValidationError` or create raise_af tickets "
            "automatically.  Integrate this into CI or the `regenerate-architecture` "
            "CLI command.  Provide unit tests for the validator."
        ),
    ),
    (
        "Add retrieval API endpoints for memory and architecture search",
        "src/actifix/api.py:800",
        "Feature",
        "P2",
        (
            "Extend `api.py` with new endpoints:\n"
            "  - GET /api/memory/search?query=...&top_k=n: accepts a vector or text "
            "query, runs similarity search via `ContextEmbeddingRepo` and returns "
            "the matching chunks and metadata.\n"
            "  - GET /api/memory/conversation/<thread_id>: returns the "
            "conversation history for the given thread across sessions.\n"
            "  - GET /api/architecture/modules: returns a list of modules with "
            "metrics and summaries, optionally filtered by domain or owner.\n"
            "  - GET /api/architecture/dependencies?module=<module_id>: returns "
            "dependencies of a module from the enriched DEPGRAPH.\n"
            "Add appropriate authentication and rate limiting via existing "
            "security modules.  Document the new endpoints in the API docs and "
            "update any client code."
        ),
    ),
]


def create_tickets() -> None:
    """Iterate through the TICKETS list and record each one."""
    for i, (message, source, error_type, priority, ai_notes) in enumerate(TICKETS, start=1):
        print(f"[{i}/{len(TICKETS)}] Creating ticket: {message}")
        # Map priority string to the TicketPriority enum
        try:
            priority_enum = getattr(TicketPriority, priority)
        except AttributeError:
            # Fall back to P3 if priority is unknown
            priority_enum = TicketPriority.P3

        entry = record_error(
            message=message,
            source=source,
            run_label="context-graph-update",
            error_type=error_type,
            priority=priority_enum,
            skip_duplicate_check=True,
            skip_ai_notes=True,
        )

        if entry is None:
            # Duplicate or failure; skip updating notes
            print(f"  Skipped duplicate or failed to create: {message}")
            continue

        # Update the AI remediation notes directly in the database
        repo = get_ticket_repository()
        try:
            repo.update_ticket(entry.entry_id, {"ai_remediation_notes": ai_notes})
            print(f"  Updated AI notes for {entry.entry_id}")
        except Exception as e:
            print(f"  Failed to update AI notes for {entry.entry_id}: {e}")


def main() -> None:
    create_tickets()


if __name__ == "__main__":
    main()
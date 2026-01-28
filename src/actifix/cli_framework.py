"""
CLI Framework - Unified interactive CLI for Actifix.

Provides guided workflows, interactive prompts, structured output, and
command chaining for terminal-based interactions. Consolidates 30+
CLI-related tickets into a single, reusable framework.
"""

from __future__ import annotations

import sys
from typing import Optional, List, Dict, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class OutputLevel(Enum):
    """Output verbosity levels."""
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


@dataclass
class CLIColors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @classmethod
    def header(cls, text: str) -> str:
        return f"{cls.BOLD}{cls.HEADER}{text}{cls.ENDC}"

    @classmethod
    def success(cls, text: str) -> str:
        return f"{cls.OKGREEN}✓ {text}{cls.ENDC}"

    @classmethod
    def error(cls, text: str) -> str:
        return f"{cls.FAIL}✗ {text}{cls.ENDC}"

    @classmethod
    def warning(cls, text: str) -> str:
        return f"{cls.WARNING}⚠ {text}{cls.ENDC}"

    @classmethod
    def info(cls, text: str) -> str:
        return f"{cls.OKCYAN}ℹ {text}{cls.ENDC}"

    @classmethod
    def highlight(cls, text: str) -> str:
        return f"{cls.OKBLUE}{text}{cls.ENDC}"


class CLIPrompt:
    """Interactive CLI prompts for user input."""

    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """Ask for yes/no confirmation."""
        default_str = "[Y/n]" if default else "[y/N]"
        prompt = f"{message} {default_str}: "

        try:
            response = input(prompt).strip().lower()
        except EOFError:
            return default
        except KeyboardInterrupt:
            print("\nAborted")
            sys.exit(1)

        if not response:
            return default

        return response in ('y', 'yes', '1', 'true')

    @staticmethod
    def select(message: str, choices: List[str], default: int = 0) -> str:
        """Select from a list of choices."""
        print(f"\n{message}")
        for i, choice in enumerate(choices, 1):
            marker = "→" if i - 1 == default else " "
            print(f"  {marker} {i}. {choice}")

        while True:
            try:
                response = input(f"\nSelect (1-{len(choices)}, default={default + 1}): ").strip()
            except EOFError:
                return choices[default]
            except KeyboardInterrupt:
                print("\nAborted")
                sys.exit(1)

            if not response:
                return choices[default]

            try:
                idx = int(response) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
                print(f"Invalid selection. Please choose 1-{len(choices)}")
            except ValueError:
                print(f"Invalid input. Please enter a number.")

    @staticmethod
    def input_text(message: str, default: str = "") -> str:
        """Get text input from user."""
        default_str = f" [{default}]" if default else ""
        prompt = f"{message}{default_str}: "

        try:
            response = input(prompt).strip()
        except EOFError:
            return default
        except KeyboardInterrupt:
            print("\nAborted")
            sys.exit(1)

        return response if response else default

    @staticmethod
    def input_multiline(message: str, prompt_end: str = "(end with blank line)") -> str:
        """Get multi-line input from user."""
        print(f"{message} {prompt_end}")
        lines = []
        try:
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
        except EOFInterrupt:
            pass
        except KeyboardInterrupt:
            print("\nAborted")
            sys.exit(1)

        return '\n'.join(lines)


class CLIOutput:
    """Structured terminal output helpers."""

    def __init__(self, level: OutputLevel = OutputLevel.NORMAL):
        self.level = level
        self.colors = CLIColors()

    def section(self, title: str) -> None:
        """Print a section header."""
        print(f"\n{self.colors.header(title)}")
        print("=" * 80)

    def subsection(self, title: str) -> None:
        """Print a subsection header."""
        print(f"\n{self.colors.BOLD}{title}{self.colors.ENDC}")

    def success(self, message: str) -> None:
        """Print success message."""
        print(self.colors.success(message))

    def error(self, message: str) -> None:
        """Print error message."""
        print(self.colors.error(message))

    def warning(self, message: str) -> None:
        """Print warning message."""
        print(self.colors.warning(message))

    def info(self, message: str) -> None:
        """Print informational message."""
        if self.level.value >= OutputLevel.NORMAL.value:
            print(self.colors.info(message))

    def debug(self, message: str) -> None:
        """Print debug message."""
        if self.level.value >= OutputLevel.DEBUG.value:
            print(f"{self.colors.OKCYAN}[DEBUG]{self.colors.ENDC} {message}")

    def print(self, message: str, level: OutputLevel = OutputLevel.NORMAL) -> None:
        """Conditional print based on verbosity level."""
        if self.level.value >= level.value:
            print(message)

    def table(self, rows: List[List[str]], headers: Optional[List[str]] = None,
              col_widths: Optional[List[int]] = None) -> None:
        """Print a formatted table."""
        if not rows:
            return

        # Auto-calculate column widths if not provided
        if col_widths is None:
            num_cols = len(rows[0]) if rows else (len(headers) if headers else 0)
            col_widths = [10] * num_cols

            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(col_widths):
                        col_widths[i] = max(col_widths[i], len(str(cell)))

            if headers:
                for i, header in enumerate(headers):
                    if i < len(col_widths):
                        col_widths[i] = max(col_widths[i], len(header))

        # Print headers
        if headers:
            header_str = " | ".join(
                f"{h:<{col_widths[i]}}" for i, h in enumerate(headers)
            )
            print(f"\n{self.colors.BOLD}{header_str}{self.colors.ENDC}")
            print("-" * (sum(col_widths) + len(col_widths) * 3 - 1))

        # Print rows
        for row in rows:
            row_str = " | ".join(
                f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row)
            )
            print(row_str)

    def progress_bar(self, current: int, total: int, width: int = 40) -> None:
        """Print a progress bar."""
        if total <= 0:
            return

        percent = current / total
        filled = int(width * percent)
        bar = '█' * filled + '░' * (width - filled)
        pct_str = f"{percent*100:.1f}%"
        print(f"\r[{bar}] {pct_str}", end='', flush=True)


class CLIWorkflow:
    """Guided workflow for multi-step CLI interactions."""

    def __init__(self, name: str, output: Optional[CLIOutput] = None):
        self.name = name
        self.output = output or CLIOutput()
        self.steps: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}

    def add_step(self, name: str, handler: Callable, description: str = "") -> CLIWorkflow:
        """Add a workflow step."""
        self.steps.append({
            'name': name,
            'handler': handler,
            'description': description,
        })
        return self

    def run(self) -> Dict[str, Any]:
        """Execute the workflow."""
        self.output.section(f"Workflow: {self.name}")

        total = len(self.steps)
        for i, step in enumerate(self.steps, 1):
            try:
                self.output.subsection(f"Step {i}/{total}: {step['name']}")
                if step['description']:
                    self.output.print(f"  {step['description']}")

                result = step['handler'](self.context)
                self.context[step['name']] = result

                self.output.success(f"{step['name']} completed")
            except Exception as e:
                self.output.error(f"{step['name']} failed: {e}")
                if not CLIPrompt.confirm("Continue anyway?", default=False):
                    raise

        self.output.section("Workflow Complete")
        return self.context


class CLICommand:
    """Base class for CLI commands with guided interaction."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.output = CLIOutput()
        self.guided = True  # Enable guided mode by default

    def get_help(self) -> str:
        """Get help text for this command."""
        return f"{self.name}: {self.description}"

    def run(self, args: Any) -> int:
        """Execute the command. Override in subclasses."""
        raise NotImplementedError()

    def confirm_action(self, action: str) -> bool:
        """Confirm an action with the user."""
        if not self.guided:
            return True
        return CLIPrompt.confirm(f"Do you want to {action}?", default=False)


class CLIDiagnostic:
    """Diagnostic tools for CLI troubleshooting."""

    def __init__(self, output: Optional[CLIOutput] = None):
        self.output = output or CLIOutput(OutputLevel.VERBOSE)

    def diagnose_path(self, path: Union[str, Path]) -> None:
        """Diagnose issues with a file path."""
        path = Path(path)
        self.output.subsection(f"Diagnosing: {path}")

        if path.exists():
            self.output.success(f"Path exists")
            if path.is_file():
                self.output.print(f"  Type: File")
                self.output.print(f"  Size: {path.stat().st_size} bytes")
            elif path.is_dir():
                self.output.print(f"  Type: Directory")
                try:
                    items = list(path.iterdir())
                    self.output.print(f"  Contents: {len(items)} items")
                except PermissionError:
                    self.output.warning("Cannot read directory contents (permission denied)")
        else:
            self.output.error(f"Path does not exist")
            parent = path.parent
            if parent.exists():
                self.output.info(f"Parent directory exists: {parent}")
            else:
                self.output.warning(f"Parent directory also does not exist: {parent}")

    def diagnose_database(self, db_path: Union[str, Path]) -> None:
        """Diagnose database connectivity and integrity."""
        db_path = Path(db_path)
        self.output.subsection(f"Diagnosing Database: {db_path}")

        self.diagnose_path(db_path)

        if db_path.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                self.output.success(f"Database is readable")
                self.output.print(f"  Tables: {table_count}")
                conn.close()
            except Exception as e:
                self.output.error(f"Cannot read database: {e}")


# Utility functions for common CLI patterns
def run_guided_command(name: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run a guided command with multiple steps."""
    workflow = CLIWorkflow(name)
    for step in steps:
        workflow.add_step(step['name'], step['handler'], step.get('description', ''))
    return workflow.run()


def format_tickets_table(tickets: List[Dict[str, Any]]) -> None:
    """Format and display a table of tickets."""
    output = CLIOutput()

    headers = ["ID", "Priority", "Type", "Status"]
    rows = []

    for ticket in tickets:
        rows.append([
            ticket.get('id', '')[:12],
            ticket.get('priority', ''),
            ticket.get('error_type', '')[:15],
            ticket.get('status', ''),
        ])

    output.table(rows, headers=headers, col_widths=[15, 4, 18, 10])

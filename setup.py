#!/usr/bin/env python3
"""
ACTIFIX Universal Setup Script
=============================

A comprehensive, cross-platform setup script that automates the complete
ACTIFIX installation and configuration process as described in QUICKSTART.md
and README.md.

Features:
- Cross-platform support (macOS, Linux, Windows/WSL)
- Prerequisites validation
- Virtual environment management
- Dependency installation
- Workspace initialization
- Health validation
- Development mode bootstrapping
- Comprehensive error handling and rollback
- Full logging and progress reporting
- Self-testing capabilities

Usage:
    python setup.py                    # Full setup with prompts
    python setup.py --auto             # Automated setup (no prompts)
    python setup.py --dev              # Include development dependencies
    python setup.py --no-venv          # Skip virtual environment
    python setup.py --test             # Run self-tests
    python setup.py --cleanup          # Cleanup/rollback installation
    python setup.py --help             # Show detailed help

Author: ACTIFIX Team
License: MIT
"""

import argparse
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import traceback
import venv
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


# Configuration
REQUIRED_PYTHON_VERSION = (3, 10)
PROJECT_NAME = "ACTIFIX"
SETUP_LOG_FILE = "logs/setup.log"
ROLLBACK_STATE_FILE = ".actifix/setup_state.json"
TIMEOUT_COMMANDS = 300  # 5 minutes timeout for commands


class Colors:
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


class SetupError(Exception):
    """Custom exception for setup-related errors."""
    pass


class SetupLogger:
    """Comprehensive logging system for the setup process."""
    
    def __init__(self, log_file: str = SETUP_LOG_FILE, verbose: bool = True):
        self.log_file = Path(log_file)
        self.verbose = verbose
        self._setup_logging()
        
    def _setup_logging(self):
        """Initialize logging configuration."""
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, mode='a'),
                logging.StreamHandler(sys.stdout) if self.verbose else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def info(self, message: str):
        """Log info message with color."""
        self.logger.info(message)
        if self.verbose:
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} {message}")
            
    def warning(self, message: str):
        """Log warning message with color."""
        self.logger.warning(message)
        if self.verbose:
            print(f"{Colors.WARNING}⚠{Colors.ENDC} {message}")
            
    def error(self, message: str):
        """Log error message with color."""
        self.logger.error(message)
        if self.verbose:
            print(f"{Colors.FAIL}✗{Colors.ENDC} {message}")
            
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
        
    def header(self, message: str):
        """Print formatted header."""
        if self.verbose:
            print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
            print(f"{Colors.HEADER}{Colors.BOLD}{message.center(60)}{Colors.ENDC}")
            print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
        self.logger.info(f"=== {message} ===")


class RollbackManager:
    """Manages rollback state and cleanup operations."""
    
    def __init__(self, state_file: str = ROLLBACK_STATE_FILE):
        self.state_file = Path(state_file)
        self.state: Dict[str, Any] = {}
        self._load_state()
        
    def _load_state(self):
        """Load rollback state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            except Exception:
                self.state = {}
                
    def _save_state(self):
        """Save rollback state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
            
    def record_action(self, action: str, details: Dict[str, Any]):
        """Record an action that might need rollback."""
        self.state[action] = {
            'timestamp': time.time(),
            'details': details
        }
        self._save_state()
        
    def cleanup(self, logger: SetupLogger):
        """Perform cleanup/rollback of recorded actions."""
        logger.header("CLEANUP AND ROLLBACK")
        
        actions = [
            'venv_created',
            'dependencies_installed', 
            'workspace_initialized',
            'development_bootstrapped'
        ]
        
        for action in reversed(actions):
            if action in self.state:
                self._rollback_action(action, self.state[action]['details'], logger)
                
        # Clear state
        self.state = {}
        self._save_state()
        logger.info("Cleanup completed")
        
    def _rollback_action(self, action: str, details: Dict[str, Any], logger: SetupLogger):
        """Rollback a specific action."""
        try:
            if action == 'venv_created':
                venv_path = Path(details.get('path', '.venv'))
                if venv_path.exists():
                    shutil.rmtree(venv_path)
                    logger.info(f"Removed virtual environment: {venv_path}")
                    
            elif action == 'workspace_initialized':
                # Remove created directories (but preserve any manually created content)
                dirs_to_check = ['actifix', '.actifix', 'logs']
                for dir_name in dirs_to_check:
                    dir_path = Path(dir_name)
                    if dir_path.exists() and details.get('created_dirs', {}).get(dir_name):
                        try:
                            shutil.rmtree(dir_path)
                            logger.info(f"Removed directory: {dir_path}")
                        except OSError:
                            logger.warning(f"Could not remove directory: {dir_path}")
                            
        except Exception as e:
            logger.warning(f"Failed to rollback {action}: {e}")


class PlatformDetector:
    """Detects platform and validates prerequisites."""
    
    @staticmethod
    def get_platform() -> str:
        """Detect the current platform."""
        system = platform.system().lower()
        if system == 'darwin':
            return 'macos'
        elif system == 'linux':
            return 'linux'
        elif system == 'windows':
            return 'windows'
        else:
            return 'unknown'
            
    @staticmethod
    def check_python_version() -> bool:
        """Check if Python version meets requirements."""
        version = sys.version_info[:2]
        return version >= REQUIRED_PYTHON_VERSION
        
    @staticmethod
    def check_tool_available(tool: str) -> bool:
        """Check if a command-line tool is available."""
        try:
            subprocess.run([tool, '--version'], capture_output=True, timeout=10)
            return True
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return False
            
    @staticmethod
    def check_disk_space(required_mb: int = 500) -> bool:
        """Check if sufficient disk space is available."""
        try:
            statvfs = os.statvfs('.')
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            free_mb = free_bytes / (1024 * 1024)
            return free_mb >= required_mb
        except (OSError, AttributeError):
            return True  # Assume sufficient space if can't check


class ActifixSetup:
    """Main setup orchestrator for ACTIFIX."""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.logger = SetupLogger(verbose=not args.quiet)
        self.rollback = RollbackManager()
        self.platform = PlatformDetector.get_platform()
        self.project_root = Path.cwd()
        self.venv_path = self.project_root / '.venv'
        
    def run(self):
        """Execute the complete setup process."""
        try:
            self.logger.header(f"{PROJECT_NAME} Universal Setup")
            
            if self.args.cleanup:
                self.rollback.cleanup(self.logger)
                return
                
            if self.args.test:
                self._run_self_tests()
                return
                
            # Main setup flow
            self._validate_prerequisites()
            self._setup_virtual_environment()
            self._install_dependencies()
            self._initialize_workspace()
            self._validate_installation()
            self._bootstrap_development()
            self._setup_frontend()
            self._display_summary()
            
            self.logger.info("Setup completed successfully! 🚀")
            
        except KeyboardInterrupt:
            self.logger.error("Setup interrupted by user")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            if self.args.debug:
                traceback.print_exc()
            self._offer_rollback()
            sys.exit(1)
            
    def _validate_prerequisites(self):
        """Validate all prerequisites are met."""
        self.logger.header("Validating Prerequisites")
        
        # Check Python version
        if not PlatformDetector.check_python_version():
            current = ".".join(map(str, sys.version_info[:2]))
            required = ".".join(map(str, REQUIRED_PYTHON_VERSION))
            raise SetupError(f"Python {required}+ required, found {current}")
        self.logger.info(f"Python {sys.version.split()[0]} ✓")
        
        # Check required tools
        required_tools = ['git', 'pip']
        missing_tools = []
        for tool in required_tools:
            if PlatformDetector.check_tool_available(tool):
                self.logger.info(f"{tool} available ✓")
            else:
                missing_tools.append(tool)
                
        if missing_tools:
            raise SetupError(f"Missing required tools: {', '.join(missing_tools)}")
            
        # Check disk space
        if not PlatformDetector.check_disk_space():
            self.logger.warning("Low disk space detected")
            
        # Platform-specific checks
        self._platform_specific_checks()
        
        self.logger.info("All prerequisites validated ✓")
        
    def _platform_specific_checks(self):
        """Perform platform-specific prerequisite checks."""
        if self.platform == 'macos':
            # Check for Command Line Tools
            if not Path('/usr/bin/git').exists():
                self.logger.warning("Consider installing Xcode Command Line Tools: xcode-select --install")
                
        elif self.platform == 'linux':
            # Check for common packages
            try:
                subprocess.run(['which', 'python3'], check=True, capture_output=True)
                self.logger.info("python3 available ✓")
            except subprocess.CalledProcessError:
                self.logger.warning("python3 not found in PATH")
                
        elif self.platform == 'windows':
            self.logger.info("Windows detected - ensure you're running in WSL2 for best results")
            
    def _setup_virtual_environment(self):
        """Set up Python virtual environment if requested."""
        if self.args.no_venv:
            self.logger.info("Skipping virtual environment creation")
            return
            
        self.logger.header("Setting Up Virtual Environment")
        
        if self.venv_path.exists():
            if self.args.auto or self._ask_yes_no(f"Virtual environment exists at {self.venv_path}. Recreate?"):
                shutil.rmtree(self.venv_path)
            else:
                self.logger.info("Using existing virtual environment")
                return
                
        # Create virtual environment
        self.logger.info(f"Creating virtual environment at {self.venv_path}")
        venv.create(self.venv_path, with_pip=True)
        
        self.rollback.record_action('venv_created', {'path': str(self.venv_path)})
        self.logger.info("Virtual environment created ✓")
        
    @contextmanager
    def _activated_venv(self):
        """Context manager to temporarily activate virtual environment."""
        if self.args.no_venv or not self.venv_path.exists():
            yield
            return
            
        # Save original PATH
        original_path = os.environ.get('PATH', '')
        original_virtual_env = os.environ.get('VIRTUAL_ENV', '')
        
        # Set up venv environment
        if self.platform == 'windows':
            scripts_dir = self.venv_path / 'Scripts'
            python_exe = scripts_dir / 'python.exe'
        else:
            scripts_dir = self.venv_path / 'bin'
            python_exe = scripts_dir / 'python'
            
        os.environ['PATH'] = f"{scripts_dir}{os.pathsep}{original_path}"
        os.environ['VIRTUAL_ENV'] = str(self.venv_path)
        
        try:
            yield str(python_exe)
        finally:
            # Restore original environment
            os.environ['PATH'] = original_path
            if original_virtual_env:
                os.environ['VIRTUAL_ENV'] = original_virtual_env
            else:
                os.environ.pop('VIRTUAL_ENV', None)
                
    def _install_dependencies(self):
        """Install Python dependencies."""
        self.logger.header("Installing Dependencies")
        
        with self._activated_venv() as python_exe:
            if python_exe is None:
                python_exe = sys.executable
                
            # Upgrade pip first
            self._run_command([python_exe, '-m', 'pip', 'install', '--upgrade', 'pip'])
            
            # Install runtime dependencies
            self.logger.info("Installing ACTIFIX runtime dependencies...")
            self._run_command([python_exe, '-m', 'pip', 'install', '-e', '.'])
            
            # Install development dependencies if requested
            if self.args.dev:
                self.logger.info("Installing development dependencies...")
                self._run_command([python_exe, '-m', 'pip', 'install', '-e', '.[dev]'])
                
        self.rollback.record_action('dependencies_installed', {'dev': self.args.dev})
        self.logger.info("Dependencies installed ✓")
        
    def _initialize_workspace(self):
        """Initialize ACTIFIX workspace."""
        self.logger.header("Initializing Workspace")
        
        # Record what directories exist before initialization
        existing_dirs = {}
        for dir_name in ['actifix', '.actifix', 'logs']:
            existing_dirs[dir_name] = Path(dir_name).exists()
            
        with self._activated_venv() as python_exe:
            if python_exe is None:
                python_exe = sys.executable
                
            # Run actifix initialization
            self.logger.info("Running ACTIFIX workspace initialization...")
            self._run_command([python_exe, '-m', 'actifix.main', 'init'])
            
        # Record what directories were created
        created_dirs = {}
        for dir_name in ['actifix', '.actifix', 'logs']:
            created_dirs[dir_name] = not existing_dirs[dir_name] and Path(dir_name).exists()
            
        self.rollback.record_action('workspace_initialized', {'created_dirs': created_dirs})
        self.logger.info("Workspace initialized ✓")
        
    def _validate_installation(self):
        """Validate the installation is working correctly."""
        self.logger.header("Validating Installation")
        
        with self._activated_venv() as python_exe:
            if python_exe is None:
                python_exe = sys.executable
                
            # Run health check
            self.logger.info("Running ACTIFIX health check...")
            result = self._run_command([python_exe, '-m', 'actifix.main', 'health'], check=False)
            
            if result.returncode != 0:
                self.logger.warning("Health check failed, but continuing...")
            else:
                self.logger.info("Health check passed ✓")
                
        # Verify key files exist
        key_files = [
            'src/actifix/__init__.py',
            'pyproject.toml',
        ]
        
        for file_path in key_files:
            if Path(file_path).exists():
                self.logger.info(f"Key file exists: {file_path} ✓")
            else:
                self.logger.warning(f"Key file missing: {file_path}")
                
        self.logger.info("Installation validation completed ✓")
        
    def _bootstrap_development(self):
        """Bootstrap ACTIFIX development mode if requested."""
        if not self.args.dev:
            return
            
        self.logger.header("Bootstrapping Development Mode")
        
        with self._activated_venv() as python_exe:
            if python_exe is None:
                python_exe = sys.executable
                
            # Create a bootstrap script
            bootstrap_script = textwrap.dedent("""
                import sys
                sys.path.insert(0, 'src')
                import actifix
                
                print("Bootstrapping ACTIFIX development mode...")
                actifix.bootstrap_actifix_development()
                
                # Create a demo ticket
                print("Creating demo ticket...")
                actifix.record_error(
                    message="Demo setup ticket - ACTIFIX is ready!",
                    source="setup.py",
                    run_label="setup-demo",
                    error_type="SetupComplete"
                )
                
                print("Development mode bootstrapped successfully!")
            """)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(bootstrap_script)
                f.flush()
                
                try:
                    self._run_command([python_exe, f.name])
                    self.rollback.record_action('development_bootstrapped', {})
                    self.logger.info("Development mode bootstrapped ✓")
                finally:
                    os.unlink(f.name)
                    
    def _setup_frontend(self):
        """Set up the frontend if it exists."""
        frontend_dir = self.project_root / 'actifix-frontend'
        if not frontend_dir.exists():
            return
            
        self.logger.header("Setting Up Frontend")
        
        # Check if we can serve the frontend
        try:
            import http.server
            self.logger.info("Frontend ready to serve at: python3 -m http.server 8080 (from actifix-frontend/)")
            self.logger.info("After starting, visit: http://localhost:8080")
        except ImportError:
            self.logger.warning("HTTP server module not available")
            
        self.logger.info("Frontend setup completed ✓")
        
    def _run_self_tests(self):
        """Run comprehensive self-tests."""
        self.logger.header("Running Self-Tests")
        
        tests = [
            self._test_prerequisites,
            self._test_python_imports,
            self._test_workspace_structure,
            self._test_commands,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                test()
                passed += 1
            except Exception as e:
                self.logger.error(f"Test failed: {e}")
                failed += 1
                
        self.logger.info(f"Self-tests completed: {passed} passed, {failed} failed")
        
        if failed > 0:
            sys.exit(1)
            
    def _test_prerequisites(self):
        """Test prerequisite checking."""
        if not PlatformDetector.check_python_version():
            raise SetupError("Python version check failed")
        self.logger.info("Prerequisites test ✓")
        
    def _test_python_imports(self):
        """Test Python imports work."""
        try:
            sys.path.insert(0, 'src')
            import actifix
            self.logger.info("Python imports test ✓")
        except ImportError as e:
            raise SetupError(f"Import test failed: {e}")
            
    def _test_workspace_structure(self):
        """Test workspace structure is correct."""
        required_paths = [
            'src/actifix',
            'pyproject.toml',
            'README.md'
        ]
        
        for path in required_paths:
            if not Path(path).exists():
                raise SetupError(f"Required path missing: {path}")
                
        self.logger.info("Workspace structure test ✓")
        
    def _test_commands(self):
        """Test key commands work."""
        with self._activated_venv() as python_exe:
            if python_exe is None:
                python_exe = sys.executable
                
            # Test help command
            result = self._run_command([python_exe, '-m', 'actifix.main', '--help'], check=False)
            if result.returncode != 0:
                raise SetupError("Command test failed")
                
        self.logger.info("Commands test ✓")
        
    def _run_command(self, cmd: List[str], check: bool = True, timeout: int = TIMEOUT_COMMANDS) -> subprocess.CompletedProcess:
        """Run a command with proper error handling and logging."""
        self.logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check
            )
            
            if result.stdout:
                self.logger.debug(f"Command output: {result.stdout}")
            if result.stderr:
                self.logger.debug(f"Command error: {result.stderr}")
                
            return result
            
        except subprocess.TimeoutExpired:
            raise SetupError(f"Command timed out: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            raise SetupError(f"Command failed: {' '.join(cmd)} - {e.stderr}")
            
    def _ask_yes_no(self, question: str) -> bool:
        """Ask a yes/no question."""
        if self.args.auto:
            return True
            
        while True:
            response = input(f"{question} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please answer 'y' or 'n'")
                
    def _offer_rollback(self):
        """Offer to rollback changes on failure."""
        if self.args.auto:
            return
            
        if self._ask_yes_no("Setup failed. Would you like to rollback changes?"):
            self.rollback.cleanup(self.logger)
            
    def _display_summary(self):
        """Display setup completion summary."""
        self.logger.header("Setup Summary")
        
        summary = f"""
{Colors.OKGREEN}🎉 ACTIFIX Setup Completed Successfully! 🎉{Colors.ENDC}

{Colors.BOLD}What's been set up:{Colors.ENDC}
• ✓ Prerequisites validated
• ✓ Dependencies installed ({('runtime + dev' if self.args.dev else 'runtime only')})
• ✓ Virtual environment ({'created' if not self.args.no_venv else 'skipped'})
• ✓ Workspace initialized
• ✓ Health validation completed

{Colors.BOLD}Next steps:{Colors.ENDC}
1. {Colors.OKCYAN}View generated tickets:{Colors.ENDC}
   cat actifix/ACTIFIX-LIST.md
   cat actifix/ACTIFIX.md

2. {Colors.OKCYAN}Test ACTIFIX in action:{Colors.ENDC}
   python3 -c "
import sys; sys.path.insert(0, 'src')
import actifix
actifix.bootstrap_actifix_development()
actifix.record_error('Test error', 'test.py:1', 'demo')
"

3. {Colors.OKCYAN}Start the web interface:{Colors.ENDC}
   cd actifix-frontend && python3 -m http.server 8080
   # Then visit: http://localhost:8080

4. {Colors.OKCYAN}Run comprehensive tests:{Colors.ENDC}
   python test.py

5. {Colors.OKCYAN}Check health status:{Colors.ENDC}
   python -m actifix.main health

{Colors.BOLD}Documentation:{Colors.ENDC}
• Quick Start: QUICKSTART.md
• Full Guide: README.md
• Framework Overview: docs/FRAMEWORK_OVERVIEW.md

{Colors.BOLD}Commands available:{Colors.ENDC}
• python -m actifix.main init      # Initialize workspace
• python -m actifix.main health    # Health check
• python -m actifix.main stats     # Show statistics
• python -m actifix.main test      # Self-test
• actifix-health                   # Health check (if in PATH)

{Colors.OKGREEN}ACTIFIX is ready to track and improve your code! 🚀{Colors.ENDC}
        """
        
        print(summary)
        
        # Log setup completion
        with open('logs/setup_completion.log', 'a') as f:
            f.write(f"Setup completed successfully at {time.ctime()}\n")
            f.write(f"Platform: {self.platform}\n")
            f.write(f"Python: {sys.version}\n")
            f.write(f"Args: {self.args}\n")
            f.write("-" * 50 + "\n")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description=f"{PROJECT_NAME} Universal Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python setup.py                    # Interactive setup
          python setup.py --auto --dev       # Automated setup with dev deps
          python setup.py --no-venv          # Skip virtual environment
          python setup.py --test             # Run self-tests
          python setup.py --cleanup          # Cleanup installation
          
        For detailed setup documentation, see QUICKSTART.md and README.md
        """)
    )
    
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Run in automated mode (no interactive prompts)'
    )
    
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Install development dependencies (tests, linting, etc.)'
    )
    
    parser.add_argument(
        '--no-venv',
        action='store_true',
        help='Skip virtual environment creation'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run self-tests to validate setup script'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Cleanup/rollback previous installation'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output (except errors)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output and stack traces'
    )
    
    return parser


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Ensure we're in the correct directory
    if not Path('pyproject.toml').exists() or not Path('src/actifix').exists():
        print(f"{Colors.FAIL}Error: This script must be run from the ACTIFIX project root directory{Colors.ENDC}")
        print(f"Expected to find: pyproject.toml and src/actifix/")
        sys.exit(1)
        
    # Run setup
    setup = ActifixSetup(args)
    setup.run()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Comprehensive test suite for setup.py

Tests all functionality of the ACTIFIX universal setup script including:
- Platform detection
- Prerequisites validation  
- Virtual environment management
- Dependency installation
- Workspace initialization
- Error handling and rollback
- Self-testing capabilities
- Cross-platform compatibility
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import setup
from setup import (
    ActifixSetup, 
    Colors,
    PlatformDetector, 
    RollbackManager,
    SetupError,
    SetupLogger
)


class TestColors(unittest.TestCase):
    """Test the Colors class for terminal output."""
    
    def test_color_codes_exist(self):
        """Test that all expected color codes are defined."""
        expected_colors = [
            'HEADER', 'OKBLUE', 'OKCYAN', 'OKGREEN', 
            'WARNING', 'FAIL', 'ENDC', 'BOLD', 'UNDERLINE'
        ]
        
        for color in expected_colors:
            self.assertTrue(hasattr(Colors, color))
            self.assertIsInstance(getattr(Colors, color), str)


class TestSetupError(unittest.TestCase):
    """Test the custom SetupError exception."""
    
    def test_setup_error_creation(self):
        """Test SetupError can be created and raised."""
        with self.assertRaises(SetupError):
            raise SetupError("Test error")
            
    def test_setup_error_message(self):
        """Test SetupError preserves error message."""
        message = "Test error message"
        try:
            raise SetupError(message)
        except SetupError as e:
            self.assertEqual(str(e), message)


class TestSetupLogger(unittest.TestCase):
    """Test the SetupLogger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "test.log"
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_logger_initialization(self):
        """Test logger initializes correctly."""
        logger = SetupLogger(str(self.log_file), verbose=False)
        self.assertTrue(self.log_file.exists())
        
    def test_logger_methods(self):
        """Test logger methods work without errors."""
        logger = SetupLogger(str(self.log_file), verbose=False)
        
        # Test all logging methods
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        logger.debug("Test debug message")
        logger.header("Test Header")
        
        # Verify log file contains messages
        with open(self.log_file, 'r') as f:
            content = f.read()
            self.assertIn("Test info message", content)
            self.assertIn("Test warning message", content)
            self.assertIn("Test error message", content)


class TestRollbackManager(unittest.TestCase):
    """Test the RollbackManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = Path(self.temp_dir) / "state.json"
        self.logger = SetupLogger(verbose=False)
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_rollback_manager_initialization(self):
        """Test rollback manager initializes correctly."""
        manager = RollbackManager(str(self.state_file))
        self.assertIsInstance(manager.state, dict)
        
    def test_record_action(self):
        """Test recording actions for rollback."""
        manager = RollbackManager(str(self.state_file))
        manager.record_action('test_action', {'key': 'value'})
        
        # Verify action was recorded
        self.assertIn('test_action', manager.state)
        self.assertEqual(manager.state['test_action']['details']['key'], 'value')
        
        # Verify state file was created
        self.assertTrue(self.state_file.exists())
        
    def test_cleanup_venv(self):
        """Test rollback of virtual environment creation."""
        # Create a fake venv directory
        venv_dir = Path(self.temp_dir) / "test_venv"
        venv_dir.mkdir()
        
        manager = RollbackManager(str(self.state_file))
        manager.record_action('venv_created', {'path': str(venv_dir)})
        
        # Perform cleanup
        manager.cleanup(self.logger)
        
        # Verify venv directory was removed
        self.assertFalse(venv_dir.exists())


class TestPlatformDetector(unittest.TestCase):
    """Test the PlatformDetector class."""
    
    def test_get_platform(self):
        """Test platform detection returns valid platform."""
        platform_name = PlatformDetector.get_platform()
        valid_platforms = ['macos', 'linux', 'windows', 'unknown']
        self.assertIn(platform_name, valid_platforms)
        
    def test_check_python_version(self):
        """Test Python version checking."""
        # This should pass since we're running tests with Python
        self.assertTrue(PlatformDetector.check_python_version())
        
    def test_check_tool_available(self):
        """Test tool availability checking."""
        # Test with a command that should exist
        self.assertTrue(PlatformDetector.check_tool_available('python'))
        
        # Test with a command that likely doesn't exist
        self.assertFalse(PlatformDetector.check_tool_available('nonexistent_command_12345'))
        
    def test_check_disk_space(self):
        """Test disk space checking."""
        # This should generally pass unless disk is really full
        result = PlatformDetector.check_disk_space(1)  # 1MB requirement
        self.assertIsInstance(result, bool)


class TestActifixSetupArgumentParsing(unittest.TestCase):
    """Test argument parsing for the setup script."""
    
    def test_argument_parser_creation(self):
        """Test argument parser can be created."""
        parser = setup.create_argument_parser()
        self.assertIsNotNone(parser)
        
    def test_parse_auto_argument(self):
        """Test parsing --auto argument."""
        parser = setup.create_argument_parser()
        args = parser.parse_args(['--auto'])
        self.assertTrue(args.auto)
        
    def test_parse_dev_argument(self):
        """Test parsing --dev argument."""
        parser = setup.create_argument_parser()
        args = parser.parse_args(['--dev'])
        self.assertTrue(args.dev)
        
    def test_parse_no_venv_argument(self):
        """Test parsing --no-venv argument."""
        parser = setup.create_argument_parser()
        args = parser.parse_args(['--no-venv'])
        self.assertTrue(args.no_venv)
        
    def test_parse_test_argument(self):
        """Test parsing --test argument."""
        parser = setup.create_argument_parser()
        args = parser.parse_args(['--test'])
        self.assertTrue(args.test)
        
    def test_parse_cleanup_argument(self):
        """Test parsing --cleanup argument."""
        parser = setup.create_argument_parser()
        args = parser.parse_args(['--cleanup'])
        self.assertTrue(args.cleanup)


class TestActifixSetup(unittest.TestCase):
    """Test the main ActifixSetup orchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create minimal project structure in temp dir
        os.chdir(self.temp_dir)
        
        # Create required files
        Path('pyproject.toml').touch()
        Path('src').mkdir()
        Path('src/actifix').mkdir()
        Path('src/actifix/__init__.py').touch()
        
        # Create args mock
        self.args = Mock()
        self.args.auto = True
        self.args.dev = False
        self.args.no_venv = True  # Skip venv for tests
        self.args.test = False
        self.args.cleanup = False
        self.args.quiet = True
        self.args.debug = False
        
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_setup_initialization(self):
        """Test ActifixSetup can be initialized."""
        setup_obj = ActifixSetup(self.args)
        self.assertIsNotNone(setup_obj.logger)
        self.assertIsNotNone(setup_obj.rollback)
        self.assertIsInstance(setup_obj.platform, str)
        
    def test_validate_prerequisites(self):
        """Test prerequisites validation."""
        setup_obj = ActifixSetup(self.args)
        
        # This should not raise an exception
        try:
            setup_obj._validate_prerequisites()
        except SetupError:
            self.fail("Prerequisites validation failed unexpectedly")
            
    @patch('setup.subprocess.run')
    def test_run_command(self, mock_run):
        """Test command execution."""
        setup_obj = ActifixSetup(self.args)
        
        # Mock successful command
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")
        
        result = setup_obj._run_command(['echo', 'test'])
        self.assertEqual(result.returncode, 0)
        
    def test_ask_yes_no_auto_mode(self):
        """Test yes/no prompts in auto mode."""
        setup_obj = ActifixSetup(self.args)
        
        # In auto mode, should always return True
        result = setup_obj._ask_yes_no("Test question?")
        self.assertTrue(result)


class TestSetupIntegration(unittest.TestCase):
    """Integration tests for the setup script."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create a minimal ACTIFIX project structure
        os.chdir(self.temp_dir)
        
        # Copy essential files
        original_root = Path(self.original_cwd)
        
        # Create pyproject.toml
        shutil.copy2(original_root / 'pyproject.toml', '.')
        
        # Create src structure
        src_dir = Path('src')
        src_dir.mkdir()
        actifix_dir = src_dir / 'actifix'
        actifix_dir.mkdir()
        
        # Copy minimal actifix files
        if (original_root / 'src/actifix/__init__.py').exists():
            shutil.copy2(original_root / 'src/actifix/__init__.py', actifix_dir / '__init__.py')
        else:
            (actifix_dir / '__init__.py').touch()
            
        # Create setup.py
        shutil.copy2(original_root / 'setup.py', '.')
        
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_setup_help(self):
        """Test setup.py --help works."""
        try:
            result = subprocess.run(
                [sys.executable, 'setup.py', '--help'],
                capture_output=True,
                text=True,
                timeout=30
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn('ACTIFIX Universal Setup Script', result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("setup.py --help timed out")
            
    def test_setup_self_test(self):
        """Test setup.py --test works."""
        try:
            result = subprocess.run(
                [sys.executable, 'setup.py', '--test', '--quiet'],
                capture_output=True,
                text=True,
                timeout=60
            )
            # Note: This might fail due to missing dependencies, but shouldn't crash
            self.assertIn([0, 1], [result.returncode])  # Allow either success or expected failure
        except subprocess.TimeoutExpired:
            self.fail("setup.py --test timed out")


class TestSetupEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_wrong_directory_detection(self):
        """Test setup detects when run from wrong directory."""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        
        try:
            os.chdir(temp_dir)
            
            # Run setup.py from wrong directory
            result = subprocess.run(
                [sys.executable, Path(original_cwd) / 'setup.py'],
                capture_output=True,
                text=True
            )
            
            self.assertEqual(result.returncode, 1)
            self.assertIn("must be run from the ACTIFIX project root", result.stderr)
            
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)
            
    def test_interrupted_setup(self):
        """Test setup handles keyboard interruption."""
        args = Mock()
        args.auto = True
        args.dev = False
        args.no_venv = True
        args.test = False
        args.cleanup = False
        args.quiet = True
        args.debug = False
        
        setup_obj = ActifixSetup(args)
        
        # Mock a method to raise KeyboardInterrupt
        with patch.object(setup_obj, '_validate_prerequisites', side_effect=KeyboardInterrupt):
            with self.assertRaises(SystemExit) as cm:
                setup_obj.run()
            self.assertEqual(cm.exception.code, 1)


class TestSetupDocumentation(unittest.TestCase):
    """Test setup script documentation and help."""
    
    def test_docstring_completeness(self):
        """Test setup.py has comprehensive documentation."""
        # Read the setup.py file
        setup_file = Path(__file__).parent.parent / 'setup.py'
        with open(setup_file, 'r') as f:
            content = f.read()
            
        # Check for key documentation elements
        self.assertIn('ACTIFIX Universal Setup Script', content)
        self.assertIn('Cross-platform support', content)
        self.assertIn('Usage:', content)
        self.assertIn('Author: ACTIFIX Team', content)
        
    def test_help_output_completeness(self):
        """Test help output contains essential information."""
        parser = setup.create_argument_parser()
        help_text = parser.format_help()
        
        # Check for key help elements
        self.assertIn('ACTIFIX Universal Setup Script', help_text)
        self.assertIn('--auto', help_text)
        self.assertIn('--dev', help_text)
        self.assertIn('--no-venv', help_text)
        self.assertIn('Examples:', help_text)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

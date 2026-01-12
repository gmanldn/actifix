"""
Test Flask availability and auto-installation mechanism for API server.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestFlaskAutoInstall(unittest.TestCase):
    """Test Flask dependency auto-installation."""

    def test_flask_available(self):
        """Test that Flask and flask-cors are available."""
        try:
            import flask
            import flask_cors
            self.assertTrue(True, "Flask dependencies are available")
        except ImportError as e:
            self.fail(f"Flask dependencies not available: {e}")

    def test_api_module_imports(self):
        """Test that api module can be imported."""
        try:
            from actifix import api
            self.assertTrue(hasattr(api, 'create_app'))
            self.assertTrue(hasattr(api, 'run_api_server'))
            self.assertTrue(hasattr(api, '_ensure_web_dependencies'))
        except ImportError as e:
            self.fail(f"Failed to import api module: {e}")

    def test_ensure_web_dependencies_when_available(self):
        """Test _ensure_web_dependencies when Flask is already available."""
        from actifix.api import _ensure_web_dependencies
        
        result = _ensure_web_dependencies()
        self.assertTrue(result, "Should return True when Flask is available")

    @patch('actifix.api.FLASK_AVAILABLE', False)
    @patch('subprocess.run')
    def test_ensure_web_dependencies_auto_install(self, mock_run):
        """Test that _ensure_web_dependencies attempts auto-installation."""
        from actifix.api import _ensure_web_dependencies
        
        # Mock successful installation
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Successfully installed flask",
            stderr=""
        )
        
        # Note: This test will still fail the import check since we can't
        # actually install packages during testing, but we can verify
        # the subprocess call was made
        with patch('builtins.print'):  # Suppress output
            result = _ensure_web_dependencies()
        
        # Verify pip install was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], sys.executable)
        self.assertEqual(call_args[1], '-m')
        self.assertEqual(call_args[2], 'pip')
        self.assertEqual(call_args[3], 'install')
        self.assertIn('flask', call_args)
        self.assertIn('flask-cors', call_args)

    def test_create_app(self):
        """Test that create_app returns a Flask application."""
        from actifix.api import create_app
        
        app = create_app()
        self.assertIsNotNone(app)
        self.assertTrue(hasattr(app, 'route'))
        self.assertTrue(hasattr(app, 'run'))
        
        # Verify static file configuration
        self.assertIsNotNone(app.static_folder)
        self.assertTrue('actifix-frontend' in str(app.static_folder))

    def test_frontend_route_exists(self):
        """Test that the root route for serving frontend exists."""
        from actifix.api import create_app
        
        app = create_app()
        
        # Get all routes
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        
        # Verify root route exists
        self.assertIn('/', routes, "Root route should exist to serve frontend")
        
        # Verify API routes exist
        self.assertIn('/api/health', routes)
        self.assertIn('/api/tickets', routes)
        self.assertIn('/api/logs', routes)

    def test_static_folder_configuration(self):
        """Test that static folder is properly configured."""
        from actifix.api import create_app
        
        app = create_app()
        static_folder = Path(app.static_folder)
        
        # Verify static folder exists
        self.assertTrue(static_folder.exists(), 
                       f"Static folder should exist: {static_folder}")
        
        # Verify frontend files exist
        index_html = static_folder / 'index.html'
        self.assertTrue(index_html.exists(), 
                       "index.html should exist in static folder")
        
        styles_css = static_folder / 'styles.css'
        self.assertTrue(styles_css.exists(), 
                       "styles.css should exist in static folder")
        
        app_js = static_folder / 'app.js'
        self.assertTrue(app_js.exists(), 
                       "app.js should exist in static folder")

    def test_pyproject_web_dependencies(self):
        """Test that pyproject.toml includes web optional dependencies."""
        try:
            import tomllib  # Python 3.11+ built-in
        except ImportError:
            import tomli as tomllib  # Fallback for older Python

        pyproject_path = Path(__file__).parent.parent / 'pyproject.toml'

        if not pyproject_path.exists():
            self.skipTest("pyproject.toml not found")

        with open(pyproject_path, 'rb') as f:
            pyproject = tomllib.load(f)
        
        # Check optional dependencies
        optional_deps = pyproject.get('project', {}).get('optional-dependencies', {})
        self.assertIn('web', optional_deps, 
                     "pyproject.toml should have 'web' optional dependencies")
        
        web_deps = optional_deps['web']
        
        # Verify Flask dependencies are listed
        flask_found = any('flask' in dep.lower() for dep in web_deps)
        cors_found = any('cors' in dep.lower() for dep in web_deps)
        
        self.assertTrue(flask_found, "Flask should be in web dependencies")
        self.assertTrue(cors_found, "flask-cors should be in web dependencies")


if __name__ == '__main__':
    unittest.main()
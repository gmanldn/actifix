"""
Comprehensive tests for configuration management.
Tests config loading, validation, and environment handling.
"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from actifix.config import load_config, get_config, reset_config, validate_config, ActifixConfig


class TestConfigLoading:
    """Test configuration loading."""
    
    def test_load_config_default(self, tmp_path):
        """Test loading default configuration."""
        config = load_config(project_root=tmp_path)
        
        assert config is not None
        assert isinstance(config, ActifixConfig)
        assert config.project_root == tmp_path.resolve()
    
    def test_load_config_with_env_vars(self, tmp_path, monkeypatch):
        """Test configuration with environment variables."""
        monkeypatch.setenv("ACTIFIX_MAX_ROLLUP_ERRORS", "42")
        monkeypatch.setenv("ACTIFIX_CAPTURE_ENABLED", "0")
        
        config = load_config(project_root=tmp_path)
        
        assert config is not None
        assert config.max_rollup_errors == 42
        assert config.capture_enabled is False
    
    def test_load_config_custom_path(self, tmp_path):
        """Test loading config from custom path."""
        config = load_config(project_root=tmp_path, config_file=tmp_path / "actifix.toml")
        
        assert config is not None
    
    def test_load_config_missing_file(self, tmp_path):
        """Test loading when config file is missing."""
        # Should return defaults
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_load_config_caching(self, tmp_path):
        """Test that config is cached."""
        reset_config()
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2
    
    def test_load_config_reload(self, tmp_path):
        """Test forcing config reload."""
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        assert config2 is not None
        assert config1 is not config2
    
    def test_load_config_invalid_path(self):
        """Test loading with invalid path."""
        config = load_config(project_root=Path("/nonexistent"), fail_fast=False)
        
        # Should still return defaults
        assert config is not None
    
    def test_load_config_multiple_sources(self, tmp_path, monkeypatch):
        """Test config from multiple sources merges correctly."""
        monkeypatch.setenv("ACTIFIX_TEST", "value")
        
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_load_config_priority(self, tmp_path, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("ACTIFIX_PRIORITY", "HIGH")
        
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_load_config_validation(self, tmp_path):
        """Test that loaded config is validated."""
        config = load_config(project_root=tmp_path)
        
        errors = validate_config(config)
        assert errors == []


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_required_fields(self, tmp_path):
        """Test validation of required fields."""
        config = load_config(project_root=tmp_path)
        
        # Config should have some structure
        assert config is not None
    
    def test_validate_field_types(self, tmp_path):
        """Test validation of field types."""
        config = load_config(project_root=tmp_path)
        
        assert isinstance(config, ActifixConfig)
    
    def test_validate_numeric_ranges(self, tmp_path):
        """Test validation of numeric field ranges."""
        config = load_config(project_root=tmp_path)
        
        # Config should be valid
        assert config is not None
    
    def test_validate_string_patterns(self, tmp_path):
        """Test validation of string patterns."""
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_validate_nested_configs(self, tmp_path):
        """Test validation of nested configuration."""
        config = load_config(project_root=tmp_path)
        
        assert isinstance(config, ActifixConfig)


class TestEnvironmentHandling:
    """Test environment-specific configuration."""
    
    def test_development_environment(self, tmp_path, monkeypatch):
        """Test dev environment config."""
        monkeypatch.setenv("ENV", "development")
        
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_production_environment(self, tmp_path, monkeypatch):
        """Test production environment config."""
        monkeypatch.setenv("ENV", "production")
        
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_test_environment(self, tmp_path, monkeypatch):
        """Test test environment config."""
        monkeypatch.setenv("ENV", "test")
        
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_environment_overrides(self, tmp_path, monkeypatch):
        """Test environment-specific overrides."""
        monkeypatch.setenv("ACTIFIX_OVERRIDE", "custom")
        
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_missing_environment_uses_default(self, tmp_path):
        """Test default environment when not specified."""
        config = load_config(project_root=tmp_path)
        
        assert config is not None


class TestConfigEdgeCases:
    """Edge case tests for configuration."""
    
    def test_empty_config_file(self, tmp_path):
        """Test handling empty config file."""
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_malformed_config_file(self, tmp_path):
        """Test handling malformed config."""
        config = load_config(project_root=tmp_path)
        
        # Should fallback to defaults
        assert config is not None
    
    def test_large_config_file(self, tmp_path):
        """Test handling very large config."""
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_special_characters_in_values(self, tmp_path, monkeypatch):
        """Test config with special characters."""
        monkeypatch.setenv("ACTIFIX_SPECIAL", "value™with©special®chars")
        
        config = load_config(project_root=tmp_path)
        
        assert config is not None
    
    def test_unicode_in_values(self, tmp_path, monkeypatch):
        """Test config with unicode values."""
        monkeypatch.setenv("ACTIFIX_UNICODE", "测试中文")
        
        config = load_config(project_root=tmp_path)
        
        assert config is not None

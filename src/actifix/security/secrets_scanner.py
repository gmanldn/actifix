#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Secrets Scanner - Detect leaked secrets before commit.

Scans staged files for common secret patterns:
- API keys (OpenAI, AWS, Azure, etc.)
- Private keys (RSA, SSH, EC)
- Tokens and credentials (Bearer, JWT, etc.)
- Database connection strings
- Passwords and sensitive data

Version: 1.0.0
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Set
from pathlib import Path


@dataclass
class SecretMatch:
    """Represents a detected secret in a file."""

    file_path: str
    line_number: int
    secret_type: str
    context: str  # Line of code containing the secret
    severity: str  # high, medium, low


class SecretsScanner:
    """Scanner for detecting leaked secrets in files."""

    # Secret patterns - ordered by severity
    SECRET_PATTERNS = {
        # High severity: Private keys
        'rsa_private_key': {
            'pattern': r'-----BEGIN RSA PRIVATE KEY-----',
            'severity': 'high',
        },
        'openssh_private_key': {
            'pattern': r'-----BEGIN OPENSSH PRIVATE KEY-----',
            'severity': 'high',
        },
        'ec_private_key': {
            'pattern': r'-----BEGIN EC PRIVATE KEY-----',
            'severity': 'high',
        },
        'pgp_private_key': {
            'pattern': r'-----BEGIN PGP PRIVATE KEY BLOCK-----',
            'severity': 'high',
        },

        # High severity: API keys
        'openai_api_key': {
            'pattern': r'sk-[a-zA-Z0-9]{20,}',
            'severity': 'high',
        },
        'aws_access_key': {
            'pattern': r'AKIA[0-9A-Z]{16}',
            'severity': 'high',
        },
        'aws_secret_key': {
            'pattern': r'(aws_secret_access_key|aws_secret)\s*=\s*["\']?([A-Za-z0-9/+=]{40})',
            'severity': 'high',
        },
        'github_token': {
            'pattern': r'ghp_[A-Za-z0-9_]{20,}',
            'severity': 'high',
        },
        'github_oauth': {
            'pattern': r'ghu_[A-Za-z0-9_]{20,}',
            'severity': 'high',
        },
        'github_app_token': {
            'pattern': r'ghs_[A-Za-z0-9_]{20,}',
            'severity': 'high',
        },
        'azure_storage_key': {
            'pattern': r'DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[^;]+',
            'severity': 'high',
        },
        'google_api_key': {
            'pattern': r'AIza[0-9A-Za-z_-]{30,}',
            'severity': 'high',
        },
        'mailchimp_api_key': {
            'pattern': r'[0-9a-f]{32}-us[0-9]{1,2}',
            'severity': 'high',
        },
        'slack_api_token': {
            'pattern': r'xox[baprs]-[0-9]{6,}-[0-9]{6,}-[a-zA-Z0-9]{16,}',
            'severity': 'high',
        },
        'stripe_api_key': {
            'pattern': r'sk_live_[A-Za-z0-9]{24}',
            'severity': 'high',
        },
        'stripe_restricted_api_key': {
            'pattern': r'rk_live_[A-Za-z0-9]{24}',
            'severity': 'high',
        },

        # High severity: Tokens and authentication
        'bearer_token': {
            'pattern': r'bearer\s+[A-Za-z0-9\-._~+/]+=*',
            'severity': 'high',
        },
        'jwt_token': {
            'pattern': r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
            'severity': 'high',
        },
        'personal_access_token': {
            'pattern': r'pat_[A-Za-z0-9]{20,}',
            'severity': 'high',
        },

        # Medium severity: Database and connection strings
        'database_url': {
            'pattern': r'(postgres|mysql|mongodb|mssql)://[^:\s]+:[^@\s]+@',
            'severity': 'medium',
        },
        'mongodb_connection_string': {
            'pattern': r'mongodb\+srv://[^:]+:[^@]+@',
            'severity': 'medium',
        },

        # Medium severity: Passwords in code
        'hardcoded_password': {
            'pattern': r'(password|passwd|pwd)\s*[=:]\s*["\']([^"\']+)["\']',
            'severity': 'medium',
        },
        'hardcoded_api_secret': {
            'pattern': r'(api_secret|secret|api_key|apikey)\s*[=:]\s*["\']([a-zA-Z0-9/+=\-_]{20,})["\']',
            'severity': 'medium',
        },

        # Low severity: Suspicious patterns
        'env_var_assignment': {
            'pattern': r'export\s+(AWS_|OPENAI_|GITHUB_|STRIPE_)[A-Z_]+\s*=\s*[^\s]+',
            'severity': 'low',
        },
    }

    # File extensions to scan
    SCANNABLE_EXTENSIONS = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.java',
        '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
        '.kt', '.scala', '.sh', '.bash', '.env', '.env.example',
        '.yaml', '.yml', '.json', '.xml', '.toml', '.ini', '.cfg',
        '.config', '.conf', '.dockerfile', '.Dockerfile', '.gradle',
        '.maven', '.properties', '.gradle.kts', '.pem', '.key', '.crt',
        '.cert', '.txt', '.md', '.markdown', '.gitignore', '.dockerignore',
    }

    # Directories to skip
    SKIP_DIRS = {
        '.git', '.github', '.venv', 'venv', 'node_modules', '__pycache__',
        '.pytest_cache', '.mypy_cache', 'dist', 'build', 'target',
        '.idea', '.vscode', '.env', '.bundle', '.cargo', '.cocoapods',
    }

    # Common false positives to skip
    FALSE_POSITIVE_PATTERNS = {
        # Documentation and comments
        r'(EXAMPLE|SAMPLE|TEMPLATE|TODO|FIXME)',
        # Test data
        r'test_',
        r'mock_',
        r'dummy_',
        # Documentation strings
        r'(https?://)',
        # Actual variable names
        r'(password|secret|token)\s*:', # YAML keys
    }

    def __init__(self, verbose: bool = False):
        """Initialize the secrets scanner.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict:
        """Compile regex patterns for efficiency."""
        compiled = {}
        for name, config in self.SECRET_PATTERNS.items():
            try:
                compiled[name] = {
                    'regex': re.compile(config['pattern'], re.IGNORECASE),
                    'severity': config['severity'],
                }
            except re.error as e:
                if self.verbose:
                    print(f"Warning: Failed to compile pattern {name}: {e}")
        return compiled

    def _should_skip_file(self, file_path: str) -> bool:
        """Check if a file should be skipped."""
        path = Path(file_path)

        # Skip hidden files
        if any(part.startswith('.') for part in path.parts):
            return True

        # Skip files in skip directories
        for skip_dir in self.SKIP_DIRS:
            if skip_dir in path.parts:
                return True

        # Only scan known scannable extensions
        if path.suffix and path.suffix not in self.SCANNABLE_EXTENSIONS:
            # But always scan files without extensions if they're executable
            if not path.is_file() or path.stat().st_mode & 0o111 == 0:
                return True

        return False

    def _is_false_positive(self, line: str, match: re.Match) -> bool:
        """Check if a match is likely a false positive."""
        # Check false positive patterns
        for fp_pattern in self.FALSE_POSITIVE_PATTERNS:
            if re.search(fp_pattern, line):
                return True

        # Check if it's in a comment
        if line.lstrip().startswith('#') or line.lstrip().startswith('//'):
            return True

        # Check if it's in a string literal with obvious test/sample markers
        if any(marker in line for marker in ['SAMPLE', 'EXAMPLE', 'TEST', 'MOCK', 'DUMMY']):
            return True

        return False

    def scan_file(self, file_path: str) -> List[SecretMatch]:
        """Scan a single file for secrets.

        Args:
            file_path: Path to the file to scan

        Returns:
            List of detected secrets
        """
        if self._should_skip_file(file_path):
            return []

        matches: List[SecretMatch] = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except (IOError, OSError) as e:
            if self.verbose:
                print(f"Warning: Cannot read {file_path}: {e}")
            return []

        for line_num, line in enumerate(lines, 1):
            # Check all patterns
            for pattern_name, pattern_config in self.compiled_patterns.items():
                regex = pattern_config['regex']

                if regex.search(line):
                    # Check for false positives
                    if not self._is_false_positive(line, regex.search(line)):
                        matches.append(SecretMatch(
                            file_path=file_path,
                            line_number=line_num,
                            secret_type=pattern_name,
                            context=line.rstrip(),
                            severity=pattern_config['severity'],
                        ))

        return matches

    def scan_files(self, file_paths: List[str]) -> List[SecretMatch]:
        """Scan multiple files for secrets.

        Args:
            file_paths: List of file paths to scan

        Returns:
            List of detected secrets (combined from all files)
        """
        all_matches: List[SecretMatch] = []

        for file_path in file_paths:
            matches = self.scan_file(file_path)
            all_matches.extend(matches)

        return all_matches

    def scan_directory(self, directory: str) -> List[SecretMatch]:
        """Scan a directory recursively for secrets.

        Args:
            directory: Directory to scan

        Returns:
            List of detected secrets
        """
        all_matches: List[SecretMatch] = []
        dir_path = Path(directory)

        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                matches = self.scan_file(str(file_path))
                all_matches.extend(matches)

        return all_matches


def scan_git_staged_files() -> List[SecretMatch]:
    """Scan files staged in git for secrets.

    Returns:
        List of detected secrets in staged files
    """
    import subprocess

    # Get staged files from git
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMRTUXB'],
            capture_output=True,
            text=True,
            check=False,
        )
        staged_files = result.stdout.strip().split('\n')
        staged_files = [f for f in staged_files if f]
    except Exception:
        return []

    if not staged_files:
        return []

    # Scan staged files
    scanner = SecretsScanner(verbose=False)
    return scanner.scan_files(staged_files)


def format_scan_results(matches: List[SecretMatch]) -> str:
    """Format scan results for display.

    Args:
        matches: List of secret matches

    Returns:
        Formatted string for display
    """
    if not matches:
        return "No secrets detected."

    # Group by severity
    by_severity = {}
    for match in matches:
        if match.severity not in by_severity:
            by_severity[match.severity] = []
        by_severity[match.severity].append(match)

    output = []

    # High severity first
    for severity in ['high', 'medium', 'low']:
        if severity not in by_severity:
            continue

        matches_for_severity = by_severity[severity]
        output.append(f"\n[{severity.upper()}] {len(matches_for_severity)} secret(s):")

        for match in matches_for_severity:
            output.append(f"  {match.file_path}:{match.line_number}")
            output.append(f"    Type: {match.secret_type}")
            output.append(f"    Context: {match.context[:80]}...")

    return '\n'.join(output)

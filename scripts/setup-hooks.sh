#!/bin/bash
# Setup git hooks for Actifix development

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "🔧 Setting up Actifix pre-commit hooks..."

# Ensure hooks directory exists
mkdir -p "$HOOKS_DIR"

# Copy pre-commit hook
cp "$REPO_ROOT/scripts/pre-commit-hook.py" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "✓ Pre-commit hook installed"
echo "  - Tests will run on changed modules before each commit"
echo "  - Full suite runs for critical module changes"
echo "  - To disable: chmod -x .git/hooks/pre-commit"

# Optional: Setup other hooks as needed
echo "✓ Git hooks setup complete"

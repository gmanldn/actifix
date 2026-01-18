#!/bin/bash
# Actifix Multi-Agent Setup Script
# Creates isolated environment for an AI agent to prevent conflicts.

TIMESTAMP=$(date +%s)
AGENT_DIR=~/actifix-agent-${TIMESTAMP}
mkdir -p "${AGENT_DIR}/data" "${AGENT_DIR}/logs"

cat << EOF > "${AGENT_DIR}/agent.env"
# Isolated Actifix Agent Configuration Template
export ACTIFIX_DATA_DIR="${AGENT_DIR}"
export ACTIFIX_STATE_DIR="${AGENT_DIR}/.actifix"
export ACTIFIX_LOGS_DIR="${AGENT_DIR}/logs"
export ACTIFIX_CHANGE_ORIGIN=raise_af
EOF

echo "✅ Agent environment created: ${AGENT_DIR}"
echo "💡 Source the config: source ${AGENT_DIR}/agent.env"
echo "📋 View tickets: python3 scripts/view_tickets.py"
echo "🔄 Process ticket: python3 Do_AF.py 1"
echo "💻 Manual fix: Follow AGENTS.md workflow"
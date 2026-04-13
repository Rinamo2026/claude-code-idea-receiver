#!/usr/bin/env bash
# Default project initialization template for idea-receiver.
# Called as: bash init-project.sh <project_path> [--git]
#
# Customize this script or point INIT_PROJECT_SCRIPT to your own.
# This template creates a Claude Code-ready project scaffold.

set -euo pipefail

PROJECT_PATH="$1"
DO_GIT=false
if [[ "${2:-}" == "--git" ]]; then
    DO_GIT=true
fi

PROJECT_NAME="$(basename "$PROJECT_PATH")"

# --- Create directory structure ---
mkdir -p "$PROJECT_PATH/memory"
mkdir -p "$PROJECT_PATH/.claude/rules"

# --- git init ---
if $DO_GIT; then
    git init "$PROJECT_PATH" --quiet
fi

# --- .gitignore ---
cat > "$PROJECT_PATH/.gitignore" << 'GITIGNORE'
# Claude Code
.claude/settings.local.json
.claude_start.sh
.claude_start.ps1

# Python
__pycache__/
*.pyc
.venv/
venv/

# Node
node_modules/

# OS
.DS_Store
Thumbs.db
GITIGNORE

# --- memory/index.md ---
# The /start command reads memory/index.md, so we seed it here.
cat > "$PROJECT_PATH/memory/index.md" << EOF
# Memory Index — $PROJECT_NAME

Status: No durable memory yet
EOF

echo "$PROJECT_PATH"

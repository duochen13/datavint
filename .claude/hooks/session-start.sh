#!/bin/bash
# Claude Code Session Start Hook
# Automatically loads wiki documentation at session start

WIKI_DIR="wiki"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Check if wiki directory exists
if [ ! -d "$PROJECT_ROOT/$WIKI_DIR" ]; then
    echo "ℹ️  Wiki directory not found: $WIKI_DIR"
    exit 0
fi

echo "📚 Loading DataVint Wiki..."
echo ""

# Count markdown files
WIKI_FILES=$(find "$PROJECT_ROOT/$WIKI_DIR" -name "*.md" -type f | wc -l | tr -d ' ')

echo "Found $WIKI_FILES documentation files in $WIKI_DIR/"
echo ""

# List documentation structure
echo "📖 Documentation Structure:"
echo ""

# Architecture
if [ -d "$PROJECT_ROOT/$WIKI_DIR/architecture" ]; then
    echo "  🏗️  Architecture:"
    find "$PROJECT_ROOT/$WIKI_DIR/architecture" -name "*.md" -type f -exec basename {} \; | sed 's/^/     - /'
fi

# API Documentation
if [ -d "$PROJECT_ROOT/$WIKI_DIR/api" ]; then
    echo "  🔌 API:"
    find "$PROJECT_ROOT/$WIKI_DIR/api" -name "*.md" -type f -exec basename {} \; | sed 's/^/     - /'
fi

# Features
if [ -d "$PROJECT_ROOT/$WIKI_DIR/features" ]; then
    echo "  ✨ Features:"
    find "$PROJECT_ROOT/$WIKI_DIR/features" -name "*.md" -type f -exec basename {} \; | sed 's/^/     - /'
fi

# Guides
if [ -d "$PROJECT_ROOT/$WIKI_DIR/guides" ]; then
    echo "  📋 Guides:"
    find "$PROJECT_ROOT/$WIKI_DIR/guides" -name "*.md" -type f -exec basename {} \; | sed 's/^/     - /'
fi

# Deployment
if [ -d "$PROJECT_ROOT/$WIKI_DIR/deployment" ]; then
    echo "  🚀 Deployment:"
    find "$PROJECT_ROOT/$WIKI_DIR/deployment" -name "*.md" -type f -exec basename {} \; | sed 's/^/     - /'
fi

# Notebooks
if [ -d "$PROJECT_ROOT/$WIKI_DIR/notebooks" ]; then
    echo "  📓 Notebooks:"
    find "$PROJECT_ROOT/$WIKI_DIR/notebooks" -name "*.md" -type f -exec basename {} \; | sed 's/^/     - /'
fi

# Website
if [ -d "$PROJECT_ROOT/$WIKI_DIR/website" ]; then
    echo "  🌐 Website:"
    find "$PROJECT_ROOT/$WIKI_DIR/website" -name "*.md" -type f -exec basename {} \; | sed 's/^/     - /'
fi

# Changelog
if [ -d "$PROJECT_ROOT/$WIKI_DIR/changelog" ]; then
    echo "  📜 Changelog:"
    find "$PROJECT_ROOT/$WIKI_DIR/changelog" -name "*.md" -type f -exec basename {} \; | sed 's/^/     - /'
fi

echo ""
echo "✅ Wiki loaded. All documentation is available for Claude to reference."
echo ""
echo "💡 Tip: Ask Claude to summarize any doc, e.g., 'Summarize the architecture doc'"
echo ""

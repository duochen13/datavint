#!/bin/bash
# Auto-load memory files at session start

MEMORY_DIR="memory"

if [ -d "$MEMORY_DIR" ]; then
  echo "=== PROJECT MEMORY LOADED ==="
  
  for file in "$MEMORY_DIR"/*.md; do
    if [ -f "$file" ] && [ "$(basename "$file")" != "README.md" ]; then
      filename=$(basename "$file" .md)
      echo ""
      echo "## $(echo $filename | tr '[:lower:]' '[:upper:]')"
      cat "$file"
    fi
  done
  
  echo ""
  echo "=== END MEMORY ==="
fi

# Load wiki documentation
if [ -x ".claude/hooks/session-start.sh" ]; then
  ./.claude/hooks/session-start.sh
fi

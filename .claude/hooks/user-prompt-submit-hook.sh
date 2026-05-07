#!/bin/bash
# Automated Issue Review Hook
#
# This hook detects when GitHub issues are created and automatically
# triggers a comprehensive review.

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    exit 0  # Silently exit if gh not available
fi

# Try to detect if an issue was just created by checking recent issues
# Get the most recent issue (created within last 60 seconds)
RECENT_ISSUE=$(gh issue list --limit 1 --json number,createdAt --jq '.[] | select((now - (.createdAt | fromdateiso8601)) < 60) | .number' 2>/dev/null)

if [ -n "$RECENT_ISSUE" ]; then
    echo "═══════════════════════════════════════════════════════════"
    echo "🤖 AUTOMATED ISSUE REVIEW TRIGGERED"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Issue #$RECENT_ISSUE was just created. Running comprehensive review..."
    echo ""
    echo "Please review issue #$RECENT_ISSUE using the Issue Review Protocol:"
    echo ""
    echo "1. View the issue: gh issue view $RECENT_ISSUE"
    echo "2. Provide comprehensive review covering:"
    echo "   - ✅ Strengths (2-4 points)"
    echo "   - ⚠️ Concerns & Gaps (3-6 points)"
    echo "   - 🔍 Technical Feasibility Analysis"
    echo "   - 📝 Recommendations"
    echo "   - ✅ Final Verdict (Score/10)"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
fi

exit 0

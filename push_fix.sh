#!/bin/bash

# SpectrumIA - Push Fix Script
# This script pushes the requirements.txt fix to GitHub

set -e  # Exit on error

echo "🚀 SpectrumIA Fix Push Script"
echo "================================"

cd "$(dirname "$0")" || exit 1

echo "📍 Current directory: $(pwd)"
echo ""

# Check git status
echo "🔍 Git Status:"
git status --short
echo ""

# Show latest commits
echo "📝 Recent Commits:"
git log --oneline -3
echo ""

# Check if there are commits to push
AHEAD=$(git rev-list --count origin/main..main 2>/dev/null || echo "0")
echo "📤 Commits to push: $AHEAD"
echo ""

if [ "$AHEAD" -gt 0 ]; then
    echo "✅ Ready to push!"
    echo "🔄 Pushing to GitHub..."
    git push origin main -v
    echo ""
    echo "✅ Push successful!"
    echo "🎯 Next steps:"
    echo "   1. Go to: https://github.com/marccut/SpectrumIA/actions"
    echo "   2. Watch the workflows run"
    echo "   3. All 5 workflows should pass ✅"
else
    echo "⚠️  No commits to push"
    echo "   Branch is already up to date with origin/main"
fi

echo ""
echo "================================"
echo "Done!"

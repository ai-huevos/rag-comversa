#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           GIT FORENSICS: EXCAVATOR MODE ACTIVATED             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 ALL BRANCHES (local + remote):"
git branch -a -v --list
echo ""

echo "📜 COMMIT HISTORY (all branches, 60 commits):"
git log --all --oneline --graph --decorate -60
echo ""

echo "🎯 CURRENT BRANCH HEADS:"
echo "production:    $(git log -1 --oneline production 2>/dev/null || echo 'ERROR')"
echo "main:          $(git log -1 --oneline main 2>/dev/null || echo 'ERROR')"
echo "development:   $(git log -1 --oneline development 2>/dev/null || echo 'ERROR')"
echo "feat/multiagent: $(git log -1 --oneline feat/multiagent 2>/dev/null || echo 'ERROR')"
echo "feat/rag2:     $(git log -1 --oneline feat/rag2 2>/dev/null || echo 'ERROR')"
echo ""

echo "🔧 UNMERGED WORK:"
echo "feat/multiagent NOT in development:"
git log --oneline development..feat/multiagent 2>/dev/null | head -15 || echo "N/A"
echo ""
echo "feat/rag2 NOT in development:"
git log --oneline development..feat/rag2 2>/dev/null | head -15 || echo "N/A"
echo ""

echo "🏷️ TAGS:"
git tag -l -n2
echo ""

echo "✅ ANALYSIS:"
MAIN=$(git rev-parse main 2>/dev/null)
PROD=$(git rev-parse production 2>/dev/null)
if [ "$MAIN" = "$PROD" ]; then
  echo "✅ main == production (aligned)"
else
  echo "❌ main != production (diverged)"
fi

MULTIAGENT_COUNT=$(git log --oneline development..feat/multiagent 2>/dev/null | wc -l)
RAG2_COUNT=$(git log --oneline development..feat/rag2 2>/dev/null | wc -l)
echo "Unmerged: feat/multiagent=$MULTIAGENT_COUNT commits, feat/rag2=$RAG2_COUNT commits"

# Codebase Refactor Strategy Using AI Tools
**Date:** November 10, 2025  
**Goal:** Refactor system0 from scratch using EARS requirements + modern AI tools  
**Timeline:** 6-8 weeks to production-ready system

---

## Philosophy: Greenfield vs. Brownfield

### Why Refactor from Scratch?

**Current codebase issues:**
- Prompts hardcoded in extractor.py (not versioned)
- No evaluation pipeline (can't measure quality)
- No PII detection (security risk)
- Parallel processing broken (SQLite WAL issues)
- No caching (performance bottleneck)
- No user feedback loop (can't improve)

**Benefits of greenfield:**
- ✅ Clean architecture from day 1
- ✅ EARS requirements drive design
- ✅ Modern patterns (async, streaming, observability)
- ✅ Test-driven development
- ✅ Production-ready from start

**What to keep:**
- ✅ Spanish-first processing logic
- ✅ Multi-model fallback chain
- ✅ ValidationAgent patterns
- ✅ Consolidation algorithms (77% complete)
- ✅ Database schemas

---

## Tool-Specific Strategies

### Strategy 1: Perplexity Pro (Research & Architecture)

**Best for:** Understanding patterns, researching best practices

**Workflow:**
1. **Research Phase** (Week 1)
2. **Architecture Design** (Week 1-2)
3. **Technology Selection** (Week 2)

**See:** `docs/perplexity-pro-workflow.md`

### Strategy 2: Cursor + Claude (Implementation)

**Best for:** Writing production code with context

**Workflow:**
1. **Setup Phase** (Day 1)
2. **Component Implementation** (Weeks 2-5)
3. **Integration** (Week 6)

**See:** `docs/cursor-claude-workflow.md`

### Strategy 3: Gemini Pro (Code Review & Testing)

**Best for:** Finding bugs, generating tests

**Workflow:**
1. **Code Review** (Continuous)
2. **Test Generation** (Weeks 3-6)
3. **Documentation** (Week 7)

**See:** `docs/gemini-pro-workflow.md`

### Strategy 4: Claude Desktop (Requirements Discussion)

**Best for:** Interactive requirements refinement

**Workflow:**
1. **Requirements Workshop** (Week 1)
2. **Design Review** (Week 2)
3. **Sprint Planning** (Weeks 3-6)

**See:** `docs/claude-desktop-workflow.md`

---

## Recommended Approach: Hybrid Strategy

Use all tools in parallel for maximum efficiency.

**See:** `docs/hybrid-refactor-workflow.md` for complete guide.

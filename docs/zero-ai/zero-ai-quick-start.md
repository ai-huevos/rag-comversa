# Zero-AI Requirements Generation - Quick Start Guide

**Goal:** Generate EARS-compliant requirements in 30 minutes

---

## Step-by-Step Instructions

### Step 1: Open the Prompt (2 minutes)

1. Open `docs/zero-ai-requirements-generation-prompt.md`
2. Copy the ENTIRE file (Cmd+A, Cmd+C)

### Step 2: Choose Your LLM (1 minute)

**Recommended options:**

1. **Claude 3.5 Sonnet** (Best for requirements engineering)
   - Go to: https://claude.ai
   - Start new conversation
   - Paste the prompt

2. **GPT-4** (Good alternative)
   - Go to: https://chat.openai.com
   - Start new conversation
   - Paste the prompt

3. **Gemini Pro** (Budget option)
   - Go to: https://gemini.google.com
   - Start new conversation
   - Paste the prompt

### Step 3: Generate Requirements (5-10 minutes)

1. **Paste the prompt** into your chosen LLM
2. **Wait for generation** (5-10 minutes depending on LLM)
3. **Review the output** - Should be ~100-150 requirements

### Step 4: Quality Check (10 minutes)

Use this checklist to verify quality:

#### EARS Compliance
- [ ] Every requirement starts with "THE System SHALL" or uses EARS pattern
- [ ] No requirements use "SHALL not" (should be positive)
- [ ] Complex requirements follow WHERE → WHILE → WHEN/IF → THE → SHALL order
- [ ] All system names are capitalized and defined in glossary

#### INCOSE Quality
- [ ] No vague terms (quickly, adequate, reasonable, appropriate)
- [ ] No escape clauses (where possible, if feasible, as needed)
- [ ] All conditions are measurable (≥85%, <30s, etc.)
- [ ] Active voice throughout (System does X, not X is done)
- [ ] No pronouns (it, them, they)

#### Completeness
- [ ] At least 12 requirements with user stories
- [ ] At least 80 acceptance criteria total
- [ ] Covers functional requirements (extraction, validation, cost control)
- [ ] Covers non-functional requirements (performance, security, monitoring)
- [ ] Covers operational requirements (deployment, documentation)

### Step 5: Refine if Needed (5-10 minutes)

If quality check fails, ask the LLM to fix:

**Example refinement prompts:**

```
"Requirement 3.2 uses vague term 'quickly'. Please replace with measurable threshold like '<30 seconds'."

"Requirement 5.4 uses 'SHALL not'. Please rewrite as positive statement."

"Missing requirements for user feedback loop. Please add Requirement 10 with 5-7 acceptance criteria."
```

### Step 6: Save the Output (2 minutes)

1. **Copy the generated requirements** (entire document)
2. **Replace** `.kiro/specs/zero-ai/requirements.md` with new content
3. **Commit to git**:
   ```bash
   git add .kiro/specs/zero-ai/requirements.md
   git commit -m "feat: Generate EARS-compliant requirements for zero-ai"
   ```

---

## Expected Output Structure

Your generated requirements should look like this:

```markdown
# Requirements Document

## Introduction
[2-3 paragraphs about system0]

## Glossary
- **System0**: AI-powered business intelligence extraction system
- **Entity**: Structured data element extracted from interviews
- **Extraction**: Process of converting unstructured text to structured data
[... 20+ more terms]

## Requirements

### Requirement 1: Core Extraction Capability

**User Story:** As a business analyst, I want system0 to extract structured entities from Spanish interviews, so that I can analyze business intelligence without manual transcription.

#### Acceptance Criteria

1. WHEN System0 receives a Spanish interview transcript, THE System SHALL extract entities for all 17 entity types within 30 seconds.

2. THE System SHALL achieve entity extraction accuracy of at least 85 percent for pain points, processes, and systems.

3. IF extraction accuracy falls below 85 percent, THEN THE System SHALL flag the interview for manual review.

[... 7-10 more criteria]

### Requirement 2: Quality Validation
[... user story + 8-12 criteria]

### Requirement 3: Cost Control
[... user story + 5-8 criteria]

[... 9 more requirements]
```

---

## Common Issues & Fixes

### Issue 1: LLM generates narrative instead of EARS format

**Symptom:** Requirements look like "The system should extract entities accurately"

**Fix:** Add this to your prompt:
```
CRITICAL: Every requirement MUST use EARS pattern. Example:
✅ CORRECT: "THE System SHALL extract entities within 30 seconds"
❌ WRONG: "The system should extract entities quickly"
```

### Issue 2: Vague terms still present

**Symptom:** Requirements use "quickly", "adequate", "reasonable"

**Fix:** Ask LLM:
```
"Please review all requirements and replace vague terms with measurable thresholds:
- 'quickly' → '<30 seconds'
- 'adequate' → '≥85 percent'
- 'reasonable' → specific number
```

### Issue 3: Missing acceptance criteria

**Symptom:** Requirements have only 2-3 criteria each

**Fix:** Ask LLM:
```
"Please expand each requirement to have at least 5-8 acceptance criteria. 
Cover normal cases, edge cases, error cases, and performance requirements."
```

### Issue 4: No user stories

**Symptom:** Requirements jump straight to acceptance criteria

**Fix:** Ask LLM:
```
"Please add user story for each requirement using format:
'As a [role], I want [feature], so that [benefit]'"
```

---

## Time Budget

| Step | Time | Cumulative |
|------|------|------------|
| Open prompt | 2 min | 2 min |
| Choose LLM | 1 min | 3 min |
| Generate | 10 min | 13 min |
| Quality check | 10 min | 23 min |
| Refine | 5 min | 28 min |
| Save | 2 min | 30 min |

**Total: 30 minutes**

---

## Success Criteria

You're done when:

- ✅ All requirements use EARS patterns
- ✅ All criteria are measurable (numbers, not adjectives)
- ✅ At least 12 requirements with user stories
- ✅ At least 80 acceptance criteria total
- ✅ No vague terms (quickly, adequate, reasonable)
- ✅ No escape clauses (where possible, if feasible)
- ✅ Glossary defines all technical terms
- ✅ File saved to `.kiro/specs/zero-ai/requirements.md`

---

## What Happens Next?

After you have EARS-compliant requirements:

1. **Review with stakeholders** (Daniel + Comversa) - 1-2 days
2. **Create design document** using Kiro spec workflow - 3-5 days
3. **Create task list** breaking design into implementable steps - 1-2 days
4. **Implement** following the task list - 4-5 weeks

**Total timeline:** 6-7 weeks to production (January 15, 2026)

---

## Need Help?

### If generation fails:
- Try a different LLM (Claude → GPT-4 → Gemini)
- Break prompt into smaller chunks (generate 3 requirements at a time)
- Simplify prompt (remove examples, keep core instructions)

### If quality is poor:
- Use refinement prompts (see Step 5)
- Manually fix obvious issues (vague terms, missing SHALL)
- Iterate with LLM (ask for specific fixes)

### If stuck:
- Review examples in `docs/zero-ai-requirements-generation-prompt.md`
- Check enhancement plan for context: `docs/zero-ai-enhancement-plan.md`
- Read summary: `docs/zero-ai-analysis-summary.md`

---

## Pro Tips

1. **Use Claude 3.5 Sonnet** - Best at following complex instructions
2. **Generate in one shot** - Don't break into chunks (loses context)
3. **Review glossary first** - Ensures consistent terminology
4. **Check numbers** - All thresholds should match codebase reality
5. **Commit frequently** - Save progress after each refinement

---

## Ready?

**Copy this file path and open it:**
```
docs/zero-ai-requirements-generation-prompt.md
```

**Then paste the entire content into Claude/GPT-4 and hit Enter.**

**Good luck! 🚀**

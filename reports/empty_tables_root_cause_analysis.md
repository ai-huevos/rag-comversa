# Empty Tables Root Cause Analysis

**Date:** November 16, 2025
**Database:** `data/full_intelligence.db`
**Scope:** Investigation of 3 empty entity tables
**Related:** `reports/data_integrity_schema_review.md` (Issue 2)

---

## Executive Summary

**Finding:** All 3 empty tables have **functional extractors** but fail to extract entities due to:
1. **knowledge_gaps**: Overly strict keyword pre-filter (0% interview match rate)
2. **budget_constraints**: JSON parsing mismatch causing silent failures
3. **team_structures**: JSON parsing mismatch causing silent failures

**Impact:** Potentially 23-44 interviews worth of data not being captured.

**Recommendation:** Fix JSON parsing mismatch and relax keyword filters.

---

## Investigation Results

### Table 1: knowledge_gaps (0 entities)

**Extractor:** `KnowledgeGapExtractor`
**Status:** ✅ Initialized and functional
**Root Cause:** **Overly strict keyword pre-filter**

**Analysis:**
- Has pre-filter requiring specific Spanish phrases
- Required keywords: "no sé", "no sabemos", "no conozco", "desconozco", "falta capacitación", etc.
- **Match rate: 0/44 interviews (0%)**
- Pre-filter returns `[]` immediately without calling LLM
- LLM never invoked for any interview

**Code Location:**
```python
# intelligence_capture/extractors.py:3121-3125
has_gaps = any(keyword in text_lower for keyword in self.GAP_KEYWORDS)
if not has_gaps:
    return []  # ← Exits here for all 44 interviews
```

**Recommendation:**
- ✅ **Relax keyword filter** to include broader terms: "problema", "dificultad", "no funciona", "confusión"
- ✅ **Or remove pre-filter entirely** and let LLM decide
- ✅ **Or make keyword matching fuzzy/partial** instead of exact

---

### Table 2: budget_constraints (0 entities)

**Extractor:** `BudgetConstraintExtractor`
**Status:** ✅ Initialized and functional
**Root Cause:** **JSON response format mismatch**

**Analysis:**
- Has keyword pre-filter: "presupuesto", "costo", "inversión", "$", "USD", etc.
- **Match rate: 23/44 interviews (52.3%)** ✅
- LLM called for 23 interviews
- **BUT: Prompt asks for JSON array, code expects JSON object**
- Silent parsing failure returns `[]` for all interviews

**Code Location:**
```python
# intelligence_capture/extractors.py:3350-3361 (Prompt)
Return as JSON array:
[{
    "area": "what the budget is for",
    ...
}}]

# intelligence_capture/extractors.py:3371-3372 (Parsing)
result = json.loads(response.choices[0].message.content)
constraints = result.get("budget_constraints", [])  # ← Expects object, gets array
```

**Error Flow:**
1. LLM returns: `[{"area": "...", ...}]`
2. Code tries: `[...].get("budget_constraints", [])`
3. AttributeError raised (list has no .get() method)
4. Exception caught at line 3382-3384
5. Returns empty list `[]`
6. Silently fails for all 23 interviews

**Recommendation:**
- ✅ **Fix prompt** to match parsing: `{"budget_constraints": [{...}]}`
- ✅ **Or fix parsing** to handle array response
- ✅ **Add validation logging** to detect parsing failures

---

### Table 3: team_structures (0 entities)

**Extractor:** `TeamStructureExtractor`
**Status:** ✅ Initialized and functional
**Root Cause:** **JSON response format mismatch**

**Analysis:**
- **NO keyword pre-filter** - should process all interviews
- Keyword presence: 36/44 interviews (81.8%) mention team-related terms
- LLM called for all 44 interviews
- **Same JSON parsing mismatch as budget_constraints**

**Code Location:**
```python
# intelligence_capture/extractors.py:3051-3062 (Prompt)
Return as JSON array with this structure:
[{
    "role": "specific role",
    "team_size": number or null,
    ...
}}]

# intelligence_capture/extractors.py:3072-3073 (Parsing)
result = json.loads(response.choices[0].message.content)
team_structures = result.get("team_structures", [])  # ← Expects object, gets array
```

**Error Flow:** Same as budget_constraints (silent parsing failure)

**Recommendation:** Same fixes as budget_constraints

---

## Comparative Analysis

| Extractor | Pre-Filter | Keywords Found | LLM Called | Root Cause | Entities Lost |
|-----------|------------|----------------|------------|------------|---------------|
| **knowledge_gaps** | ✅ YES | 0/44 (0%) | ❌ NO | Keyword mismatch | Unknown (0-44) |
| **budget_constraints** | ✅ YES | 23/44 (52.3%) | ✅ YES | JSON parsing | 23 interviews |
| **team_structures** | ❌ NO | 36/44 (81.8%) | ✅ YES | JSON parsing | 44 interviews |
| **success_patterns** | ✅ YES | High match | ✅ YES | ✅ Working | 172 entities ✅ |

**Total Potential Data Loss:** 67-111 interviews worth of entity data (team: 44, budget: 23, gaps: 0-44)

---

## Recommended Fixes

### Priority 1: JSON Parsing Mismatch (CRITICAL)

**Impact:** 44 interviews for team_structures + 23 interviews for budget_constraints

**Fix Option A - Update Prompts:**
```python
# Change prompts to request object format
Return as JSON object:
{
    "team_structures": [{
        "role": "...",
        ...
    }]
}
```

**Fix Option B - Update Parsing:**
```python
# Handle both array and object responses
result = json.loads(response.choices[0].message.content)
if isinstance(result, list):
    team_structures = result
else:
    team_structures = result.get("team_structures", [])
```

**Recommendation:** Use Fix Option B (more robust, handles both formats)

---

### Priority 2: Knowledge Gap Keywords (MEDIUM)

**Impact:** Unknown (0-44 interviews)

**Fix Option A - Relax Keywords:**
```python
GAP_KEYWORDS = [
    # Original strict keywords
    "no sé", "no sabemos", "falta capacitación",
    # Add broader terms
    "problema", "dificultad", "no funciona", "confuso", "complicado",
    "no entiendo bien", "me cuesta", "difícil de", "necesito ayuda"
]
```

**Fix Option B - Remove Pre-Filter:**
```python
# Remove keyword check, let LLM decide
def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
    meta = interview_data.get("meta", {})
    qa_pairs = interview_data.get("qa_pairs", {})
    full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])

    # Remove keyword check
    # if not has_gaps:
    #     return []

    knowledge_gaps = self._llm_extraction(full_text, meta)
    return knowledge_gaps
```

**Recommendation:** Use Fix Option A (balance between cost and coverage)

---

### Priority 3: Validation & Monitoring (LOW)

**Add Logging:**
```python
def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
    try:
        response = self.client.chat.completions.create(...)
        result = json.loads(response.choices[0].message.content)

        # Add validation logging
        import logging
        logger = logging.getLogger(__name__)

        if isinstance(result, list):
            logger.warning(f"LLM returned array instead of object for {self.__class__.__name__}")
            entities = result
        else:
            entities = result.get("team_structures", [])

        logger.info(f"{self.__class__.__name__}: extracted {len(entities)} entities")
        return entities

    except Exception as e:
        logger.error(f"Extraction error in {self.__class__.__name__}: {e}")
        return []
```

---

## Testing Plan

### Step 1: Test Single Interview

```bash
python3 scripts/test_single_interview.py --interview-id 1
```

**Expected:**
- team_structures: 1-3 entities
- budget_constraints: 0-2 entities (if budget discussed)
- knowledge_gaps: 0-1 entities (rare, but possible)

### Step 2: Test Batch (5 interviews)

```bash
python3 scripts/test_batch_interviews.py --batch-size 5
```

**Expected:**
- team_structures: 5-15 entities
- budget_constraints: 5-10 entities
- knowledge_gaps: 0-5 entities

### Step 3: Full Extraction Run

```bash
python intelligence_capture/run.py
```

**Expected (conservative estimates):**
- team_structures: 40-100 entities (avg 1-2 per interview)
- budget_constraints: 20-40 entities (from 23 interviews with budget keywords)
- knowledge_gaps: 5-20 entities (if keywords relaxed)

---

## Implementation Priority

1. **CRITICAL (Do First):** Fix JSON parsing mismatch for team_structures and budget_constraints
2. **MEDIUM (Do Next):** Relax knowledge_gaps keyword filter
3. **LOW (Nice to Have):** Add validation logging for extraction monitoring

---

## Related Issues

- **Issue 1:** Missing company linkage ✅ **RESOLVED** (100% coverage achieved)
- **Issue 2:** Empty entity tables 🔄 **THIS DOCUMENT** (root cause identified)
- **Issue 3:** Schema inconsistencies ⏳ **PENDING** (communication_channels, department/domain naming)

---

## Validation Checklist

After implementing fixes:

- [ ] Run single interview test - verify entities extracted
- [ ] Check extraction logs for parsing errors (should be 0)
- [ ] Run batch test (5 interviews) - verify reasonable entity counts
- [ ] Full extraction run - verify all 3 tables populated
- [ ] Database validation:
  - [ ] `SELECT COUNT(*) FROM team_structures` > 0
  - [ ] `SELECT COUNT(*) FROM budget_constraints` > 0
  - [ ] `SELECT COUNT(*) FROM knowledge_gaps` >= 0 (may still be 0, acceptable)
- [ ] Company linkage validation (via interview_id FK) working
- [ ] Neo4j sync includes new entity types

---

**Last Updated:** November 16, 2025
**Status:** Root cause identified, fixes recommended, awaiting implementation

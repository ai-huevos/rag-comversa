---
inclusion: always
---

# Development Workflow & Documentation Rules

## 🚨 CRITICAL: Documentation Creation Rules

### NEVER Create These Files
❌ **Summary/recap MD files** after completing work (e.g., `CONSOLIDATION_SUMMARY.md`, `PHASE_COMPLETE.md`)
❌ **New root-level MD files** without explicit user request
❌ **Duplicate documentation** that restates what's in specs or main docs
❌ **Session handoff documents** unless specifically requested
❌ **Progress reports** as separate MD files

### ONLY Update These 4 Root Files
✅ **README.md** - Main project documentation
✅ **CLAUDE.MD** - Primary operating manual (system snapshot, status updates)
✅ **PROJECT_STRUCTURE.md** - Folder organization (add new files/directories here)
✅ **NEXT_STEPS.md** - Deployment/action guide (if it exists)

### Detailed Documentation Goes Here
✅ **`docs/`** - Feature-specific guides (e.g., `KNOWLEDGE_GRAPH_CONSOLIDATION.md`)
✅ **`.kiro/specs/{feature}/`** - Requirements, design, tasks for specs
✅ **Code comments** - Inline documentation in the code itself

### Why This Matters
- Prevents documentation bloat and duplication
- Keeps project root clean (only 4 main docs)
- Makes it easy to find information (predictable locations)
- Reduces maintenance burden

---

## 📋 Spec-Driven Development Workflow

### When Working on Specs

**File Structure:**
```
.kiro/specs/{feature-name}/
├── requirements.md  # User stories + acceptance criteria (EARS format)
├── design.md        # Architecture, components, data models
└── tasks.md         # Implementation checklist
```

**Workflow:**
1. **Requirements Phase** → Only modify `requirements.md`
2. **Design Phase** → Only modify `design.md`
3. **Tasks Phase** → Only modify `tasks.md`
4. **Implementation Phase** → Write code, update task status
5. **Completion** → Update CLAUDE.MD and PROJECT_STRUCTURE.md (NOT new MD files)

**Don't Create:**
- ❌ Additional planning documents
- ❌ Architecture diagrams as separate files (use Mermaid in design.md)
- ❌ Progress tracking files (use tasks.md checkboxes)
- ❌ Summary documents (update CLAUDE.MD instead)

---

## 💬 Response Style Rules

### After Completing Work

**DO:**
- ✅ Provide a **2-3 sentence summary** of what was accomplished
- ✅ Mention key files created/modified
- ✅ Ask what the user wants to do next

**DON'T:**
- ❌ Create markdown files to summarize work
- ❌ Write lengthy recaps with bullet point lists
- ❌ Repeat yourself (if you just said you're doing something, don't repeat)
- ❌ Create "handoff documents" unless explicitly requested

**Example - Good:**
```
Phase 5 complete! Created validation script and tested with 10 interviews. 
All tests pass, performance is under 2 minutes. What's next?
```

**Example - Bad:**
```
Let me create a summary document...
[Creates PHASE5_SUMMARY.md with 50 lines of bullet points]
```

---

## 🔄 Git Protocol

### Before Starting Work
```bash
git fetch origin
git status
git log origin/development..HEAD --oneline  # Check if ahead
git log HEAD..origin/development --oneline  # Check if behind
```

### After Completing Work
```bash
git status                    # Review changes
git add <files>              # Stage specific files
git commit -m "message"      # Commit with clear message
git push origin development  # Push to remote
```

### Commit Message Format
```
<type>: <description>

Examples:
feat: Add RelationshipDiscoverer component
fix: Correct consensus scoring formula
docs: Update CLAUDE.MD with consolidation status
test: Add integration tests for consolidation
refactor: Improve duplicate detection performance
```

---

## 📁 File Organization Rules

### Where Files Go
| Type | Location | Example |
|------|----------|---------|
| Main docs | Root (4 files only) | `README.md`, `CLAUDE.MD` |
| Feature docs | `docs/` | `KNOWLEDGE_GRAPH_CONSOLIDATION.md` |
| Scripts | `scripts/` | `validate_consolidation.py` |
| Tests | `tests/` | `test_consolidation_agent.py` |
| Reports | `reports/` | `consolidation_report.json` |
| Data | `data/` | `full_intelligence.db` |
| Config | `config/` | `consolidation_config.json` |
| Code | `intelligence_capture/` | `consolidation_agent.py` |
| Specs | `.kiro/specs/{feature}/` | `requirements.md` |

### NEVER Create Files In
❌ Project root (except the 4 main docs)
❌ Random subdirectories
❌ Temporary locations

### Always Use
✅ Path constants from `intelligence_capture/config.py`
✅ Proper subdirectories
✅ `mkdir(parents=True, exist_ok=True)` when creating files

---

## 🎯 Task Execution Rules

### When Executing Spec Tasks

**DO:**
- ✅ Mark task as "in_progress" before starting
- ✅ Focus on ONE task at a time
- ✅ Mark task as "completed" when done
- ✅ Stop and let user review before moving to next task

**DON'T:**
- ❌ Automatically proceed to next task without user approval
- ❌ Implement multiple tasks simultaneously
- ❌ Skip task status updates
- ❌ Create summary documents after each task

### Task Status Updates
```python
# Start task
taskStatus(taskFilePath="...", task="10. Create Component", status="in_progress")

# Complete task
taskStatus(taskFilePath="...", task="10. Create Component", status="completed")
```

---

## 🧪 Testing Rules

### Test Hierarchy
1. **Unit tests** - Test individual components
2. **Integration tests** - Test components working together
3. **Manual tests** - Test with real data

### Test File Naming
- `test_{component}.py` - Unit tests
- `test_{feature}_integration.py` - Integration tests

### Test Execution
```bash
# Run specific test file
pytest tests/test_consolidation_agent.py -v

# Run all tests for a feature
pytest tests/test_consolidation*.py -v

# Run with coverage
pytest --cov=intelligence_capture tests/
```

---

## 📊 Reporting Rules

### Generated Reports Go To
✅ `reports/` directory
✅ JSON format for data
✅ HTML format for dashboards
✅ Timestamped filenames: `report_20251109_123456.json`

### Don't Create
❌ Report markdown files in `docs/`
❌ Summary documents after generating reports
❌ Duplicate reports in multiple locations

---

## ✅ Quick Checklist

Before committing code:
- [ ] Files in correct directories (not root)
- [ ] No new MD files created (unless explicitly requested)
- [ ] Updated CLAUDE.MD and/or PROJECT_STRUCTURE.md if needed
- [ ] Task status updated in tasks.md
- [ ] Tests pass
- [ ] Git status reviewed

After completing work:
- [ ] Provided 2-3 sentence summary (not a new MD file)
- [ ] Asked user what's next
- [ ] Did NOT create summary/recap documents

---

**Version**: 1.0.0
**Last Updated**: 2025-11-09
**Purpose**: Prevent documentation bloat, maintain clean project structure

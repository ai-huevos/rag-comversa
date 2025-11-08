# Kiro Steering Configuration

## What is Steering?

Steering files in `.kiro/steering/` provide automatic context and instructions to Kiro for all interactions. They help maintain consistency and enforce project standards without needing to repeat instructions.

## Active Steering Rules

### 1. File Organization (`file-organization.md`)
**Status**: ✅ Active (inclusion: always)

**Purpose**: Enforces proper file placement to keep the project organized

**Key Rules**:
- Documentation → `docs/`
- Scripts → `scripts/`
- Reports → `reports/`
- Data/Databases → `data/`
- Tests → `tests/`
- Config → `config/`
- Main code → `intelligence_capture/`

**Root Directory**: Only 6 files allowed:
1. `README.md`
2. `NEXT_STEPS.md`
3. `PROJECT_STRUCTURE.md`
4. `DEPLOYMENT_COMPLETE.md`
5. `.env`
6. `.gitignore`

## How It Works

When you interact with Kiro in this project:

1. **Automatic Loading**: Steering files are automatically included in context
2. **Always Active**: Files marked `inclusion: always` are included in every interaction
3. **Enforcement**: Kiro will follow these rules when creating files
4. **Validation**: Run `python3 scripts/validate_structure.py` to verify compliance

## Verification

You can verify the steering is active by checking:

```bash
# Check steering files exist
ls -la .kiro/steering/

# Should show:
# file-organization.md
```

## Benefits

✅ **Consistency**: All files go to correct directories automatically
✅ **Clean Root**: Project root stays organized
✅ **No Repetition**: Don't need to remind Kiro about file placement
✅ **Validation**: Easy to check compliance with validation script

## Adding New Steering Rules

To add new project-specific rules:

1. Create a new file in `.kiro/steering/`
2. Add front matter:
   ```markdown
   ---
   inclusion: always
   ---
   ```
3. Write your rules in markdown
4. Kiro will automatically load it

### Example Use Cases for Additional Steering

- **Code Style**: Python formatting standards, naming conventions
- **Testing Requirements**: When to write tests, test coverage expectations
- **Documentation Standards**: How to document functions, required sections
- **Git Workflow**: Branch naming, commit message format
- **API Usage**: Rate limiting, error handling patterns

## Current Setup Status

✅ Steering directory created: `.kiro/steering/`
✅ File organization rules active: `file-organization.md`
✅ Validation script available: `scripts/validate_structure.py`
✅ Project structure documented: `PROJECT_STRUCTURE.md`

## Testing the Setup

To verify Kiro is following the rules:

1. **Ask Kiro to create a documentation file** - It should go to `docs/`
2. **Ask Kiro to create a script** - It should go to `scripts/`
3. **Run validation** - `python3 scripts/validate_structure.py`
4. **Check root directory** - Should only have 6 allowed files

## Troubleshooting

### Steering not being followed?
- Check file exists: `.kiro/steering/file-organization.md`
- Check front matter includes: `inclusion: always`
- Restart Kiro session if needed

### Files still in wrong places?
- Run: `python3 scripts/validate_structure.py`
- Move files manually if needed
- Report issue to Kiro team

## Related Documentation

- `PROJECT_STRUCTURE.md` - Complete folder structure guide
- `NEXT_STEPS.md` - Deployment and next actions
- `DEPLOYMENT_COMPLETE.md` - What's been accomplished

---

**Status**: Steering configuration complete and active! 🎯

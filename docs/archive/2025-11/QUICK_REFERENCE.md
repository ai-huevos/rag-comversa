# Quick Reference Card

## 🚀 Common Commands

### First Time Setup
```bash
# 1. Add your API key
nano .env

# 2. Check setup
python scripts/check_setup.py

# 3. Test with one interview
./scripts/run_intelligence.sh --test
```

### Running the System
```bash
# Process all interviews
./scripts/run_intelligence.sh

# Show database stats
./scripts/run_intelligence.sh --stats
```

### Querying the Database
```bash
# Open database
sqlite3 intelligence.db

# Example queries:
SELECT * FROM pain_points WHERE company='Los Tajibos' LIMIT 5;
SELECT COUNT(*) FROM pain_points WHERE severity='Critical';
SELECT name, usage_count FROM systems ORDER BY usage_count DESC;
```

## 📁 Where is Everything?

| What | Where |
|------|-------|
| Interview data | `data/interviews/analysis_output/all_interviews.json` |
| Main system | `intelligence_capture/run.py` |
| Output database | `intelligence.db` |
| API keys | `.env` |
| Setup guide | `docs/SETUP_INSTRUCTIONS.md` |
| Helper scripts | `scripts/` |

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key not set" | Edit `.env` with your real OpenAI key |
| "Module not found" | Run `source venv/bin/activate` |
| "Permission denied" | Run `chmod +x scripts/*.sh` |
| "Database locked" | Close other connections to `intelligence.db` |

## 💡 Quick Tips

**Activate virtual environment:**
```bash
source venv/bin/activate
```

**Deactivate virtual environment:**
```bash
deactivate
```

**Check what's in database:**
```bash
sqlite3 intelligence.db ".tables"
```

**Export query results to CSV:**
```bash
sqlite3 intelligence.db <<EOF
.mode csv
.output pain_points.csv
SELECT * FROM pain_points WHERE company='Los Tajibos';
.quit
EOF
```

**View database schema:**
```bash
sqlite3 intelligence.db ".schema pain_points"
```

## 📊 Useful Queries

### Pain Points by Company
```sql
SELECT company, COUNT(*) as count 
FROM pain_points 
GROUP BY company;
```

### Critical Pain Points
```sql
SELECT company, description, severity 
FROM pain_points 
WHERE severity='Critical';
```

### Most Used Systems
```sql
SELECT name, usage_count, companies_using 
FROM systems 
ORDER BY usage_count DESC 
LIMIT 10;
```

### Automation Opportunities by Impact
```sql
SELECT name, impact, complexity 
FROM automation_candidates 
WHERE impact='High' 
ORDER BY complexity;
```

### KPIs by Company
```sql
SELECT company, name, cadence 
FROM kpis 
ORDER BY company, cadence;
```

## 🎯 Cost Reference

| Action | Time | Cost |
|--------|------|------|
| Test (1 interview) | ~10 sec | ~$0.01 |
| Full (44 interviews) | ~5-10 min | ~$0.50-$1.00 |

## 📞 Help

1. **Setup issues:** `docs/SETUP_INSTRUCTIONS.md`
2. **Understanding structure:** `docs/PROJECT_ORGANIZATION.md`
3. **System overview:** `docs/INTELLIGENCE_SYSTEM_SUMMARY.md`
4. **Check setup:** `python scripts/check_setup.py`

---

**Pro Tip:** Bookmark this file for quick access to commands!

# Intelligence Capture System - Setup Instructions

## What You Need

1. **OpenAI API Key** - Get it from: https://platform.openai.com/api-keys
2. **Python 3.9+** - Already installed ✓
3. **Virtual environment** - Already created ✓

## Setup (One-Time)

### Step 1: Add Your OpenAI API Key

Open the `.env` file and replace the placeholder with your actual key:

```bash
# Edit .env file
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

**IMPORTANT:** 
- Never commit this file to git (it's already in .gitignore)
- Keep your API key secret
- This key will be used to call GPT-4 for extraction

### Step 2: Verify Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Check if everything is installed
python -c "import openai; print('✓ OpenAI package installed')"
```

## Usage

### Test with ONE interview first (recommended)

```bash
source venv/bin/activate
cd intelligence_capture
python run.py --test
```

**What this does:**
- Processes the first interview only
- Shows you what GPT-4 extracts
- Takes ~10 seconds
- Costs ~$0.01

**Look for:**
- Pain points extracted
- Processes identified
- Systems/tools found
- KPIs captured

### Process ALL interviews

Once the test looks good:

```bash
python run.py
```

**What this does:**
- Processes all 44 interviews
- Takes ~5-10 minutes
- Costs ~$0.50-$1.00
- Creates `intelligence.db` with all data

### View Statistics

```bash
python run.py --stats
```

Shows counts by company and entity type.

## What Gets Created

```
intelligence.db          # SQLite database with all extracted data
```

## Querying the Database

### Using SQLite command line:

```bash
sqlite3 intelligence.db

# Example queries:
SELECT COUNT(*) FROM pain_points WHERE company='Los Tajibos';
SELECT * FROM pain_points WHERE severity='Critical';
SELECT name, usage_count FROM systems ORDER BY usage_count DESC;
```

### Using Python:

```python
import sqlite3

conn = sqlite3.connect('intelligence.db')
cursor = conn.cursor()

# Get all critical pain points
cursor.execute("""
    SELECT company, description, severity 
    FROM pain_points 
    WHERE severity='Critical'
""")

for row in cursor.fetchall():
    print(row)
```

## Troubleshooting

### "OPENAI_API_KEY environment variable not set"
- Make sure you edited `.env` with your actual key
- Make sure you're in the virtual environment (`source venv/bin/activate`)

### "No module named 'openai'"
- Activate virtual environment: `source venv/bin/activate`
- Install packages: `pip install -r intelligence_capture/requirements.txt`

### API errors
- Check your OpenAI API key is valid
- Check you have credits in your OpenAI account
- Check your internet connection

## Cost Estimate

- **Test mode (1 interview):** ~$0.01
- **Full run (44 interviews):** ~$0.50-$1.00
- **Model used:** gpt-4o-mini (fast and cheap)

## Next Steps

After processing:
1. Query the database for insights
2. Build company-specific reports
3. Feed data to AI agents
4. Set up triggers for new interviews (Phase 2)

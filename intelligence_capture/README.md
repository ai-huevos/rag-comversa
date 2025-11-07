# Intelligence Capture System

Processes interview data and extracts structured intelligence using AI.

## What It Does

1. **Reads** interviews from `analysis_output/all_interviews.json`
2. **Extracts** structured data using GPT-4:
   - Pain points
   - Processes
   - Systems/tools
   - KPIs
   - Automation opportunities
   - Inefficiencies
3. **Stores** everything in SQLite database (`intelligence.db`)
4. **Separates** by company (Los Tajibos, Comversa, Bolivian Foods)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-key-here'
```

## Usage

### Test with one interview first:
```bash
python run.py --test
```

### Process all interviews:
```bash
python run.py
```

### Show database stats:
```bash
python run.py --stats
```

## What Happens

For each interview:
1. ✓ Extracts entities using GPT-4
2. ✓ Stores in database
3. ✓ Links to company
4. ✓ Tracks relationships

## Database Schema

- `interviews` - Raw interview data
- `pain_points` - Problems identified
- `processes` - Business processes
- `systems` - Tools and software
- `kpis` - Success metrics
- `automation_candidates` - Automation opportunities
- `inefficiencies` - Redundant/inefficient steps

## Error Handling

- **Retries**: 3 attempts for API calls
- **Duplicates**: Skips already-processed interviews
- **Failures**: Logs errors, continues processing

## Output

Database file: `intelligence.db`

You can query it with:
```bash
sqlite3 intelligence.db "SELECT * FROM pain_points WHERE company='Los Tajibos'"
```

Or use any SQLite browser tool.

## Next Steps

After processing:
1. Query the database for insights
2. Build reports by company
3. Feed data to AI agents
4. Set up triggers for new interviews

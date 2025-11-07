# System Architecture: Visual Guide

## The Complete System (Bird's Eye View)

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                              │
│  44 Spanish Interviews (JSON files)                             │
│  - Hotel Los Tajibos: 18 interviews                             │
│  - Comversa: 13 interviews                                       │
│  - Bolivian Foods: 13 interviews                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Processor (processor.py)                                │  │
│  │  - Reads interviews one by one                           │  │
│  │  - Coordinates extraction                                │  │
│  │  - Handles errors and retries                            │  │
│  └────────────┬─────────────────────────────────────────────┘  │
│               │                                                  │
│               ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  5 Extractors (extractors.py)                            │  │
│  │                                                           │  │
│  │  1. CommunicationChannelExtractor                        │  │
│  │     → Finds: WhatsApp, Outlook, Teams                    │  │
│  │     → Extracts: Purpose, SLA, participants               │  │
│  │                                                           │  │
│  │  2. DecisionPointExtractor                               │  │
│  │     → Finds: Who decides what                            │  │
│  │     → Extracts: Criteria, escalation rules               │  │
│  │                                                           │  │
│  │  3. DataFlowExtractor                                    │  │
│  │     → Finds: Data movement between systems               │  │
│  │     → Extracts: Source, target, method, pain points      │  │
│  │                                                           │  │
│  │  4. TemporalPatternExtractor                             │  │
│  │     → Finds: When things happen                          │  │
│  │     → Extracts: Frequency, time, duration                │  │
│  │                                                           │  │
│  │  5. FailureModeExtractor                                 │  │
│  │     → Finds: What goes wrong                             │  │
│  │     → Extracts: Failure, workaround, root cause          │  │
│  └────────────┬─────────────────────────────────────────────┘  │
│               │                                                  │
│               ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  GPT-4 API                                                │  │
│  │  - Reads Spanish text                                     │  │
│  │  - Extracts structured data                               │  │
│  │  - Returns JSON with confidence scores                    │  │
│  └────────────┬─────────────────────────────────────────────┘  │
└───────────────┼──────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       STORAGE LAYER                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQLite Database (intelligence.db)                        │  │
│  │                                                           │  │
│  │  17 Tables:                                               │  │
│  │  ├─ interviews (raw data)                                 │  │
│  │  ├─ pain_points (problems)                                │  │
│  │  ├─ processes (workflows)                                 │  │
│  │  ├─ systems (tools)                                       │  │
│  │  ├─ kpis (metrics)                                        │  │
│  │  ├─ automation_candidates (opportunities)                 │  │
│  │  ├─ inefficiencies (waste)                                │  │
│  │  ├─ communication_channels (how people talk) ← NEW        │  │
│  │  ├─ decision_points (who decides) ← NEW                   │  │
│  │  ├─ data_flows (where data moves) ← NEW                   │  │
│  │  ├─ temporal_patterns (when things happen) ← NEW          │  │
│  │  └─ failure_modes (what goes wrong) ← NEW                 │  │
│  └────────────┬─────────────────────────────────────────────┘  │
└───────────────┼──────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OUTPUT LAYER                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Queryable Database                                    │  │
│  │     → SQL queries for insights                            │  │
│  │     → Company-specific filtering                          │  │
│  │     → Cross-company aggregation                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  2. CEO Validation Report                                 │  │
│  │     → Confirmed priorities (high data support)            │  │
│  │     → Weak priorities (low data support)                  │  │
│  │     → Overlooked opportunities (not in CEO list)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  3. Priority Matrix                                       │  │
│  │     → Quick Wins (low effort, high impact)                │  │
│  │     → Strategic (high effort, high impact)                │  │
│  │     → Incremental (low effort, low impact)                │  │
│  │     → Reconsider (high effort, low impact)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  4. Company RAG Databases (for AI agents)                 │  │
│  │     → Hotel Los Tajibos RAG                               │  │
│  │     → Comversa RAG                                        │  │
│  │     → Bolivian Foods RAG                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow (Step by Step)

### Step 1: Interview Enters System

```
Interview JSON:
{
  "meta": {
    "company": "Hotel Los Tajibos",
    "respondent": "Juan Pérez",
    "role": "Gerente de Restaurantes"
  },
  "qa_pairs": {
    "¿Qué herramientas usas?": "Usamos WhatsApp para urgencias y Outlook para solicitudes formales. La conciliación entre Opera y SAP la hacemos manualmente cada día a las 10pm."
  }
}
```

### Step 2: Processor Coordinates Extraction

```python
processor = IntelligenceProcessor()
processor.process_interview(interview)
```

### Step 3: Each Extractor Analyzes Text

```
CommunicationChannelExtractor:
  Input: "Usamos WhatsApp para urgencias y Outlook para solicitudes formales"
  Output: [
    {
      "channel_name": "WhatsApp",
      "purpose": "urgencias",
      "response_sla_minutes": 15,
      "confidence_score": 0.90
    },
    {
      "channel_name": "Outlook",
      "purpose": "solicitudes formales",
      "response_sla_minutes": 1440,
      "confidence_score": 0.85
    }
  ]

DataFlowExtractor:
  Input: "La conciliación entre Opera y SAP la hacemos manualmente"
  Output: [
    {
      "source_system": "Opera",
      "target_system": "SAP",
      "transfer_method": "Manual",
      "pain_points": ["Doble entrada", "Propenso a errores"],
      "confidence_score": 0.92
    }
  ]

TemporalPatternExtractor:
  Input: "cada día a las 10pm"
  Output: [
    {
      "activity_name": "Conciliación Opera-SAP",
      "frequency": "Daily",
      "time_of_day": "22:00",
      "confidence_score": 0.95
    }
  ]
```

### Step 4: Database Stores Everything

```sql
-- Interview record
INSERT INTO interviews (company, respondent, role, date, raw_data)
VALUES ('Hotel Los Tajibos', 'Juan Pérez', 'Gerente de Restaurantes', '2024-11-07', '...');

-- Communication channels
INSERT INTO communication_channels (interview_id, channel_name, purpose, response_sla_minutes)
VALUES (1, 'WhatsApp', 'urgencias', 15);

INSERT INTO communication_channels (interview_id, channel_name, purpose, response_sla_minutes)
VALUES (1, 'Outlook', 'solicitudes formales', 1440);

-- Data flow
INSERT INTO data_flows (interview_id, source_system, target_system, transfer_method)
VALUES (1, 'Opera', 'SAP', 'Manual');

-- Temporal pattern
INSERT INTO temporal_patterns (interview_id, activity_name, frequency, time_of_day)
VALUES (1, 'Conciliación Opera-SAP', 'Daily', '22:00');
```

### Step 5: You Can Query It

```sql
-- Find all WhatsApp channels
SELECT * FROM communication_channels WHERE channel_name = 'WhatsApp';

-- Find all manual data flows (automation candidates)
SELECT * FROM data_flows WHERE transfer_method = 'Manual';

-- Find all daily activities
SELECT * FROM temporal_patterns WHERE frequency = 'Daily';
```

## Component Interaction Diagram

```
┌─────────────┐
│   run.py    │  ← You run this
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                    processor.py                          │
│                                                          │
│  def process_all_interviews():                          │
│      for interview in interviews:                       │
│          ┌─────────────────────────────────────┐       │
│          │  1. Read interview JSON              │       │
│          └─────────────────────────────────────┘       │
│                      │                                   │
│                      ▼                                   │
│          ┌─────────────────────────────────────┐       │
│          │  2. Call extractors                  │       │
│          │     - CommunicationChannelExtractor  │       │
│          │     - DecisionPointExtractor         │       │
│          │     - DataFlowExtractor              │       │
│          │     - TemporalPatternExtractor       │       │
│          │     - FailureModeExtractor           │       │
│          └─────────────────────────────────────┘       │
│                      │                                   │
│                      ▼                                   │
│          ┌─────────────────────────────────────┐       │
│          │  3. Store in database                │       │
│          │     db.insert_communication_channel()│       │
│          │     db.insert_decision_point()       │       │
│          │     db.insert_data_flow()            │       │
│          │     db.insert_temporal_pattern()     │       │
│          │     db.insert_failure_mode()         │       │
│          └─────────────────────────────────────┘       │
│                      │                                   │
│                      ▼                                   │
│          ┌─────────────────────────────────────┐       │
│          │  4. Track progress                   │       │
│          │     print("Processed 1/44")          │       │
│          └─────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   database.py                            │
│                                                          │
│  class IntelligenceDB:                                  │
│      def insert_communication_channel():                │
│          cursor.execute("INSERT INTO ...")              │
│                                                          │
│      def insert_decision_point():                       │
│          cursor.execute("INSERT INTO ...")              │
│                                                          │
│      def query_by_company():                            │
│          cursor.execute("SELECT * FROM ...")            │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                intelligence.db (SQLite)                  │
│                                                          │
│  Tables with actual data from 44 interviews             │
└─────────────────────────────────────────────────────────┘
```

## Extractor Deep Dive (How They Work)

```
┌─────────────────────────────────────────────────────────┐
│         CommunicationChannelExtractor                    │
│                                                          │
│  Input: "Usamos WhatsApp para urgencias"               │
│                                                          │
│  Step 1: Rule-based detection                           │
│  ┌────────────────────────────────────────────┐        │
│  │ Search for known channels:                  │        │
│  │ - WhatsApp ✓ (found)                        │        │
│  │ - Outlook ✗ (not found)                     │        │
│  │ - Teams ✗ (not found)                       │        │
│  └────────────────────────────────────────────┘        │
│                                                          │
│  Step 2: Extract context                                │
│  ┌────────────────────────────────────────────┐        │
│  │ Purpose: "urgencias" (found near WhatsApp)  │        │
│  │ SLA: "inmediato" → 15 minutes               │        │
│  └────────────────────────────────────────────┘        │
│                                                          │
│  Step 3: Call GPT-4 for deeper analysis                 │
│  ┌────────────────────────────────────────────┐        │
│  │ Prompt: "Extract communication channels     │        │
│  │          from this Spanish text"            │        │
│  │                                              │        │
│  │ GPT-4 Response:                              │        │
│  │ {                                            │        │
│  │   "channel_name": "WhatsApp",                │        │
│  │   "purpose": "Coordinar urgencias",          │        │
│  │   "participants": ["Recepción", "Ingeniería"]│        │
│  │   "response_sla": "inmediato"                │        │
│  │ }                                            │        │
│  └────────────────────────────────────────────┘        │
│                                                          │
│  Step 4: Merge and score confidence                     │
│  ┌────────────────────────────────────────────┐        │
│  │ Rule-based: 0.7 confidence                  │        │
│  │ GPT-4: 0.9 confidence                        │        │
│  │ Final: 0.9 (take highest)                   │        │
│  └────────────────────────────────────────────┘        │
│                                                          │
│  Output:                                                 │
│  {                                                       │
│    "channel_name": "WhatsApp",                          │
│    "purpose": "Coordinar urgencias",                    │
│    "response_sla_minutes": 15,                          │
│    "confidence_score": 0.9,                             │
│    "extraction_source": "interview_1_question_3"        │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
Interview Processing
       │
       ▼
┌─────────────────┐
│ Try to extract  │
└────────┬────────┘
         │
         ├─ Success? ──────────────────────┐
         │                                  │
         │                                  ▼
         │                         ┌────────────────┐
         │                         │ Store in DB    │
         │                         └────────────────┘
         │
         ├─ Low confidence (<0.7)? ────────┐
         │                                  │
         │                                  ▼
         │                         ┌────────────────┐
         │                         │ Flag for review│
         │                         │ needs_review=1 │
         │                         └────────────────┘
         │
         ├─ API error? ────────────────────┐
         │                                  │
         │                                  ▼
         │                         ┌────────────────┐
         │                         │ Retry (3x)     │
         │                         └────────┬───────┘
         │                                  │
         │                                  ├─ Success? → Store
         │                                  │
         │                                  └─ Still fails? → Log error, skip
         │
         └─ Extraction failed? ────────────┐
                                           │
                                           ▼
                                  ┌────────────────┐
                                  │ Log error      │
                                  │ Continue to    │
                                  │ next interview │
                                  └────────────────┘
```

## Configuration Flow

```
┌─────────────────────────────────────────────────────────┐
│              config/companies.json                       │
│                                                          │
│  Defines organizational structure:                      │
│  - Holding → Companies → Business Units → Departments   │
│  - Aliases (Spanish variations)                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Hierarchy Classifier                        │
│                                                          │
│  Reads interview text:                                  │
│  "Trabajo en Alimentos y Bebidas"                       │
│                                                          │
│  Matches to config:                                     │
│  "Food & Beverage" (alias: "Alimentos y Bebidas")      │
│                                                          │
│  Classifies as:                                         │
│  - Company: Hotel Los Tajibos                           │
│  - Business Unit: Food & Beverage                       │
│  - Department: (extracted from context)                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Database Storage                            │
│                                                          │
│  Every entity tagged with:                              │
│  - company_name: "Hotel Los Tajibos"                    │
│  - business_unit: "Food & Beverage"                     │
│  - department: "Restaurantes"                           │
│                                                          │
│  Enables queries like:                                  │
│  SELECT * FROM pain_points                              │
│  WHERE company='Hotel Los Tajibos'                      │
│  AND business_unit='Food & Beverage'                    │
└─────────────────────────────────────────────────────────┘
```

## Summary: The Complete Picture

**You built a 5-layer system:**

1. **Input Layer:** 44 Spanish interviews (JSON)
2. **Processing Layer:** Processor + 5 Extractors + GPT-4
3. **Storage Layer:** SQLite database with 17 tables
4. **Output Layer:** Queries, reports, RAG databases
5. **Configuration Layer:** Org structure, priorities, settings

**Data flows through:**
Interview → Processor → Extractors → GPT-4 → Database → Outputs

**You can now:**
- Query insights by company/department
- Validate CEO priorities with data
- Identify automation opportunities
- Generate reports
- Feed AI agents (Phase 2)

**This is production-ready infrastructure for AI-driven transformation.**

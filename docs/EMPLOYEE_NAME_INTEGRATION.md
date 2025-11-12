# Employee Name Data Integration Plan

## Overview
Enhanced employee data with properly parsed first and last names for all three companies in the Comversa ecosystem.

## Data Quality Summary

### Parsing Results
- **Total employees processed:** 44
- **Companies:** COMVERSA (13), BOLIVIAN FOODS (13), LOS TAJIBOS (18)
- **Success rate:** ~98% (43/44 clean parses)
- **Manual review needed:** 1 edge case (Fridda Roca)

### Naming Conventions Detected

| Company | Pattern | Example |
|---------|---------|---------|
| COMVERSA | First name(s) + Last name(s) | `Samuel Doria Medina Auza → Samuel \| Doria Medina Auza` |
| BOLIVIAN FOODS | First name(s) + Last name(s) | `Carlos Camacho → Carlos \| Camacho` |
| LOS TAJIBOS | Last name(s) + First name(s) | `Mejia Mangudo Pamela Lucia → Pamela Lucia \| Mejia Mangudo` |

### Edge Cases
1. **Fridda Roca** (LOS TAJIBOS): Uses first-name-first format, inconsistent with company convention
   - **Recommendation:** Manual verification with HR records

## System Integration Strategy

### 1. Database Schema Enhancement

#### Add to `consolidated_entities` table:
```sql
-- Add name fields to consolidated_entities
ALTER TABLE consolidated_entities
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_name TEXT,
ADD COLUMN IF NOT EXISTS full_name TEXT,
ADD COLUMN IF NOT EXISTS gc_profile TEXT,  -- GC Index profile type
ADD COLUMN IF NOT EXISTS company TEXT;

-- Create index for name searches
CREATE INDEX IF NOT EXISTS idx_consolidated_entities_names
ON consolidated_entities(last_name, first_name);

CREATE INDEX IF NOT EXISTS idx_consolidated_entities_company
ON consolidated_entities(company);
```

#### PostgreSQL/pgvector integration:
```sql
-- Add to document_chunks metadata
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS mentioned_employees JSONB;  -- Array of employee references

-- Create GIN index for employee mentions
CREATE INDEX IF NOT EXISTS idx_document_chunks_employees
ON document_chunks USING GIN (mentioned_employees);
```

### 2. Entity Extraction Enhancement

#### Update `TeamStructure` entity type in `extractor.py`:

```python
@dataclass
class TeamStructure:
    """Enhanced team structure with employee details."""
    role: str
    team_name: str
    reporting_structure: str
    interaction_patterns: List[str]

    # NEW: Employee details
    employee_name: Optional[str] = None
    employee_first_name: Optional[str] = None
    employee_last_name: Optional[str] = None
    employee_company: Optional[str] = None
    gc_profile: Optional[str] = None  # GC Index profile

    # Profile scores
    score_game_changer: Optional[int] = None
    score_strategist: Optional[int] = None
    score_implementer: Optional[int] = None
    score_polisher: Optional[int] = None
    score_play_maker: Optional[int] = None
```

### 3. New Entity Type: `Employee` (v3.0)

```python
@dataclass
class Employee:
    """
    Employee entity with GC Index profile and organizational context.

    Captures individual employee information, their role, company,
    and behavioral/cognitive profile from GC Index assessment.
    """
    # Identity
    first_name: str
    last_name: str
    full_name: str  # For display purposes

    # Organizational context
    role: str
    company: str  # COMVERSA, BOLIVIAN FOODS, LOS TAJIBOS
    department: Optional[str] = None

    # GC Index Profile
    gc_profile: str  # e.g., "Strategist/Implementer"
    profile_description: str

    # Profile dimensions (1-20 scale)
    score_game_changer: int = 0
    score_strategist: int = 0
    score_implementer: int = 0
    score_polisher: int = 0
    score_play_maker: int = 0

    # Metadata
    confidence_score: float = 1.0  # High confidence from structured data
    source: str = "gc_index_profile"
    context: str = ""

    def get_primary_profile(self) -> str:
        """Get the dominant GC Index profile dimension."""
        scores = {
            'Game Changer': self.score_game_changer,
            'Strategist': self.score_strategist,
            'Implementer': self.score_implementer,
            'Polisher': self.score_polisher,
            'Play Maker': self.score_play_maker
        }
        return max(scores, key=scores.get)

    def get_profile_strength(self) -> float:
        """Calculate overall profile strength (0-1)."""
        total_score = sum([
            self.score_game_changer,
            self.score_strategist,
            self.score_implementer,
            self.score_polisher,
            self.score_play_maker
        ])
        return min(total_score / 100.0, 1.0)  # Normalize to 0-1
```

### 4. Employee Mention Detector

Create new module: `intelligence_capture/employee_detector.py`

```python
"""
Employee mention detector for interview transcripts.

Uses fuzzy matching and context to identify employee references
in unstructured text, linking them to structured employee data.
"""

from typing import List, Tuple, Optional
import difflib
from dataclasses import dataclass
import re


@dataclass
class EmployeeMention:
    """Detected employee mention in text."""
    employee_id: str  # Unique identifier
    first_name: str
    last_name: str
    full_name: str
    company: str
    role: str

    # Mention context
    mentioned_text: str  # How they were mentioned
    context: str  # Surrounding text
    confidence: float  # 0-1 matching confidence
    position: Tuple[int, int]  # Start, end position in text


class EmployeeDetector:
    """
    Detect employee mentions in interview transcripts.

    Strategies:
    1. Exact name matching
    2. Last name only (if unambiguous)
    3. First name + role (e.g., "Gabriela from Legal")
    4. Role references (e.g., "the CFO")
    """

    def __init__(self, employee_data: List[dict]):
        """
        Initialize with cleaned employee data.

        Args:
            employee_data: List of employee records with fname, lname, role, company
        """
        self.employees = employee_data
        self._build_indices()

    def _build_indices(self):
        """Build search indices for fast lookup."""
        self.full_name_index = {
            f"{e['fname']} {e['lname']}".lower(): e
            for e in self.employees
        }

        self.last_name_index = {}
        for e in self.employees:
            lname = e['lname'].lower()
            if lname not in self.last_name_index:
                self.last_name_index[lname] = []
            self.last_name_index[lname].append(e)

        self.first_name_index = {}
        for e in self.employees:
            fname = e['fname'].lower()
            if fname not in self.first_name_index:
                self.first_name_index[fname] = []
            self.first_name_index[fname].append(e)

        self.role_index = {}
        for e in self.employees:
            role_key = self._normalize_role(e.get('Cargo', ''))
            if role_key:
                self.role_index[role_key] = e

    def _normalize_role(self, role: str) -> str:
        """Normalize role title for matching."""
        role = role.lower().strip()
        role = re.sub(r'\s+', ' ', role)
        return role

    def detect_mentions(self, text: str, context_window: int = 100) -> List[EmployeeMention]:
        """
        Detect all employee mentions in text.

        Args:
            text: Interview transcript or document text
            context_window: Characters to include around mention for context

        Returns:
            List of EmployeeMention objects
        """
        mentions = []
        text_lower = text.lower()

        # Strategy 1: Full name matching
        for full_name, employee in self.full_name_index.items():
            for match in re.finditer(re.escape(full_name), text_lower):
                start, end = match.span()
                mentions.append(EmployeeMention(
                    employee_id=self._get_employee_id(employee),
                    first_name=employee['fname'],
                    last_name=employee['lname'],
                    full_name=f"{employee['fname']} {employee['lname']}",
                    company=employee.get('Empresa', ''),
                    role=employee.get('Cargo', ''),
                    mentioned_text=text[start:end],
                    context=text[max(0, start-context_window):min(len(text), end+context_window)],
                    confidence=1.0,
                    position=(start, end)
                ))

        # Strategy 2: Last name only (if unambiguous)
        for lname, employees in self.last_name_index.items():
            if len(employees) == 1:  # Unambiguous
                employee = employees[0]
                pattern = r'\b' + re.escape(lname) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    start, end = match.span()
                    # Check if not already captured in full name
                    if not any(m.position[0] <= start <= m.position[1] for m in mentions):
                        mentions.append(EmployeeMention(
                            employee_id=self._get_employee_id(employee),
                            first_name=employee['fname'],
                            last_name=employee['lname'],
                            full_name=f"{employee['fname']} {employee['lname']}",
                            company=employee.get('Empresa', ''),
                            role=employee.get('Cargo', ''),
                            mentioned_text=text[start:end],
                            context=text[max(0, start-context_window):min(len(text), end+context_window)],
                            confidence=0.9,
                            position=(start, end)
                        ))

        # Strategy 3: Role-based matching (lower confidence)
        for role_key, employee in self.role_index.items():
            pattern = r'\b' + re.escape(role_key) + r'\b'
            for match in re.finditer(pattern, text_lower):
                start, end = match.span()
                # Check if not already captured
                if not any(m.position[0] <= start <= m.position[1] for m in mentions):
                    mentions.append(EmployeeMention(
                        employee_id=self._get_employee_id(employee),
                        first_name=employee['fname'],
                        last_name=employee['lname'],
                        full_name=f"{employee['fname']} {employee['lname']}",
                        company=employee.get('Empresa', ''),
                        role=employee.get('Cargo', ''),
                        mentioned_text=text[start:end],
                        context=text[max(0, start-context_window):min(len(text), end+context_window)],
                        confidence=0.7,
                        position=(start, end)
                    ))

        # Sort by position and deduplicate overlaps
        mentions = self._deduplicate_mentions(mentions)
        return mentions

    def _get_employee_id(self, employee: dict) -> str:
        """Generate unique employee ID."""
        company = employee.get('Empresa', 'UNK')
        lname = employee['lname'].replace(' ', '_')
        fname = employee['fname'].replace(' ', '_')
        return f"{company}_{lname}_{fname}".upper()

    def _deduplicate_mentions(self, mentions: List[EmployeeMention]) -> List[EmployeeMention]:
        """Remove overlapping mentions, keeping highest confidence."""
        if not mentions:
            return []

        mentions = sorted(mentions, key=lambda m: (m.position[0], -m.confidence))
        deduplicated = [mentions[0]]

        for mention in mentions[1:]:
            # Check if overlaps with any existing mention
            overlaps = False
            for existing in deduplicated:
                if (mention.position[0] <= existing.position[1] and
                    mention.position[1] >= existing.position[0]):
                    overlaps = True
                    # Replace if higher confidence
                    if mention.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        deduplicated.append(mention)
                    break

            if not overlaps:
                deduplicated.append(mention)

        return sorted(deduplicated, key=lambda m: m.position[0])
```

### 5. Neo4j Knowledge Graph Enhancement

#### New node type: `Employee`

```cypher
-- Create Employee nodes
CREATE CONSTRAINT employee_id IF NOT EXISTS
FOR (e:Employee) REQUIRE e.employee_id IS UNIQUE;

-- Add nodes from CSV
LOAD CSV WITH HEADERS FROM 'file:///perfiles_gc_index_completo_44_empleados_cleaned.csv' AS row
CREATE (e:Employee {
    employee_id: row.Empresa + '_' + replace(row.lname, ' ', '_') + '_' + replace(row.fname, ' ', '_'),
    first_name: row.fname,
    last_name: row.lname,
    full_name: row.fname + ' ' + row.lname,
    role: row.Cargo,
    company: row.Empresa,
    gc_profile: row.Perfil_Hipotetico_GC_Index,
    profile_description: row.Descripcion_Perfil,
    score_game_changer: toInteger(row.Score_Game_Changer),
    score_strategist: toInteger(row.Score_Strategist),
    score_implementer: toInteger(row.Score_Implementer),
    score_polisher: toInteger(row.Score_Polisher),
    score_play_maker: toInteger(row.Score_Play_Maker)
})

-- Link employees to entities they mention
MATCH (e:Employee)
MATCH (entity:Entity)
WHERE entity.name CONTAINS e.last_name OR entity.context CONTAINS e.full_name
CREATE (e)-[:MENTIONED_IN]->(entity)

-- Link employees to their company
MATCH (e:Employee)
MATCH (c:Entity {entity_type: 'Organization', name: e.company})
CREATE (e)-[:WORKS_FOR]->(c)

-- Find collaboration patterns
MATCH (e1:Employee)-[:MENTIONED_IN]->(entity:Entity)<-[:MENTIONED_IN]-(e2:Employee)
WHERE e1 <> e2
CREATE (e1)-[:COLLABORATES_WITH {
    shared_contexts: count(entity),
    confidence: 0.8
}]->(e2)
```

### 6. RAG 2.0 Query Enhancement

#### Add employee context to retrieval:

```python
async def retrieve_with_employee_context(
    query: str,
    include_gc_profiles: bool = True,
    company_filter: Optional[str] = None
) -> List[DocumentChunk]:
    """
    Enhanced retrieval with employee context.

    Args:
        query: User query
        include_gc_profiles: Include GC Index profile matching
        company_filter: Filter by company (COMVERSA, BOLIVIAN FOODS, LOS TAJIBOS)
    """
    # Standard vector search
    chunks = await vector_search(query, k=10)

    # Detect employee mentions in query
    employee_detector = EmployeeDetector(employee_data)
    query_mentions = employee_detector.detect_mentions(query)

    if query_mentions:
        # Boost chunks that mention the same employees
        for chunk in chunks:
            chunk_mentions = employee_detector.detect_mentions(chunk.content)
            overlap = set(m.employee_id for m in query_mentions) & \
                     set(m.employee_id for m in chunk_mentions)
            if overlap:
                chunk.score *= 1.5  # Boost relevance

    # Filter by company if requested
    if company_filter:
        chunks = [c for c in chunks if company_filter in c.metadata.get('company', '')]

    # Add GC profile context
    if include_gc_profiles and query_mentions:
        for mention in query_mentions:
            employee = get_employee_by_id(mention.employee_id)
            profile_context = f"\n\n**{employee.full_name}** ({employee.role}, {employee.company}): " \
                            f"{employee.gc_profile} - {employee.profile_description}"
            chunks[0].content += profile_context

    return chunks
```

### 7. Agentic RAG Tool: Employee Lookup

```python
@tool
async def lookup_employee(
    name: Optional[str] = None,
    role: Optional[str] = None,
    company: Optional[str] = None,
    gc_profile: Optional[str] = None
) -> str:
    """
    Look up employee information.

    Args:
        name: Full name, first name, or last name
        role: Job title or role
        company: COMVERSA, BOLIVIAN FOODS, or LOS TAJIBOS
        gc_profile: GC Index profile type (e.g., "Strategist")

    Returns:
        Formatted employee information with GC profile
    """
    results = []

    # Query logic here
    employees = query_employees(
        name=name,
        role=role,
        company=company,
        gc_profile=gc_profile
    )

    for emp in employees:
        results.append(f"""
**{emp.full_name}**
- **Rol:** {emp.role}
- **Empresa:** {emp.company}
- **Perfil GC:** {emp.gc_profile}
- **Descripción:** {emp.profile_description}
- **Puntuaciones:**
  - Game Changer: {emp.score_game_changer}
  - Strategist: {emp.score_strategist}
  - Implementer: {emp.score_implementer}
  - Polisher: {emp.score_polisher}
  - Play Maker: {emp.score_play_maker}
        """)

    return "\n\n".join(results) if results else "No se encontraron empleados."
```

## Implementation Roadmap

### Phase 1: Data Integration (Week 1)
1. ✅ Clean and parse employee names
2. Import cleaned CSV into PostgreSQL
3. Create `Employee` entity type
4. Backfill consolidated_entities with employee data

### Phase 2: Detection System (Week 2)
1. Implement `EmployeeDetector` class
2. Add employee mention detection to extraction pipeline
3. Update document chunk metadata with employee mentions
4. Test detection accuracy on sample interviews

### Phase 3: Graph Integration (Week 3)
1. Create Employee nodes in Neo4j
2. Link employees to mentioned entities
3. Discover collaboration patterns
4. Build employee-centric query paths

### Phase 4: RAG Enhancement (Week 4)
1. Add `lookup_employee` tool to Pydantic AI agent
2. Implement employee context boosting in retrieval
3. Create employee-focused prompt templates
4. Test with employee-centric queries

## Benefits

### 1. Enhanced Entity Resolution
- **Before:** "Gabriela mentioned a security issue" (ambiguous)
- **After:** "Gabriela Loza (Directora Legal, COMVERSA) mentioned a security issue" (precise)

### 2. Organizational Context
- Link pain points/processes to specific employees and their GC profiles
- Understand which personality types report which types of issues
- Identify patterns: "Implementers report more process inefficiencies"

### 3. Cross-Company Analysis
- Compare employee profiles across COMVERSA, BOLIVIAN FOODS, LOS TAJIBOS
- Identify organizational culture differences
- Benchmark GC Index distributions

### 4. Personalized Insights
- "Show me all pain points mentioned by Strategist-type employees"
- "What systems does Patricia Urdininea (Gerente General, BOLIVIAN FOODS) interact with?"
- "Find collaboration patterns between COMVERSA and LOS TAJIBOS employees"

### 5. Query Examples Enabled
```
❓ "¿Qué problemas menciona Gabriela Loza?"
→ Retrieves all pain points from Legal Director with her GC profile context

❓ "¿Qué perfiles GC Index trabajan más con sistemas legacy?"
→ Identifies which personality types struggle with old systems

❓ "Muéstrame todos los Game Changers de LOS TAJIBOS"
→ Lists innovative employees and their mentioned transformation ideas

❓ "¿Quién reporta más problemas de comunicación?"
→ Identifies employees mentioning communication issues, grouped by profile

❓ "Compara los perfiles de liderazgo entre las tres empresas"
→ Analyzes GC Index distributions of directors/managers across companies
```

## Cost Estimate
- **Data integration:** ~$5 (one-time, minimal LLM usage)
- **Detection system:** ~$50-100 (development + testing)
- **Graph enhancement:** ~$20 (Neo4j operations)
- **RAG updates:** ~$30 (testing queries)
- **Total:** ~$105-155

## Timeline
- **Phase 1:** 2 days
- **Phase 2:** 3-4 days
- **Phase 3:** 2-3 days
- **Phase 4:** 2 days
- **Total:** 9-11 days

## Success Metrics
1. **Detection accuracy:** ≥95% precision on employee mention detection
2. **Graph completeness:** All 44 employees linked to relevant entities
3. **Query enhancement:** 30-40% improvement in employee-centric query relevance
4. **User satisfaction:** Ability to answer "who mentioned X?" queries accurately

## Next Steps
1. Review cleaned CSV for accuracy (especially "Fridda Roca" edge case)
2. Create database migration scripts
3. Implement `EmployeeDetector` class
4. Update extraction pipeline
5. Build employee-focused Neo4j queries
6. Enhance RAG agent with employee tools

---

**Status:** Ready for implementation
**Priority:** High (enables powerful organizational analysis)
**Risk:** Low (structured data, deterministic processing)

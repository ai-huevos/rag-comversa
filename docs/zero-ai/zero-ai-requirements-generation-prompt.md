# Prompt for Generating EARS-Compliant Requirements

**Use this prompt in another LLM (Claude, GPT-4, etc.) to generate high-quality requirements for system0**

---

## Context for the LLM

You are a requirements engineer specializing in EARS (Easy Approach to Requirements Syntax) and INCOSE quality standards. Your task is to create a production-ready requirements document for **system0**, an AI-powered business intelligence extraction system.

---

## System Overview

**system0** is a Python-based system that extracts structured business intelligence from Spanish interview transcripts. It processes 44 manager interviews from 3 companies (Los Tajibos, Comversa, Bolivian Foods) and extracts 17 entity types including pain points, processes, systems, KPIs, automation candidates, and more.

### Key Components

1. **IntelligenceExtractor**: Orchestrates extraction of 17 entity types using OpenAI GPT-4o-mini with 6-model fallback chain
2. **ValidationAgent**: Checks completeness, quality, and consistency of extracted entities
3. **ExtractionMonitor**: Tracks progress, cost, and quality metrics in real-time
4. **IntelligenceDB**: SQLite database with WAL mode for storing extracted entities
5. **KnowledgeConsolidationAgent**: Merges duplicate entities and discovers relationships (77% complete)
6. **RAG 2.0 Pipeline**: Multi-format document processing with PostgreSQL + pgvector + Neo4j (in progress)

### Current Capabilities

- **Extraction**: 17 entity types from Spanish interviews (~30s per interview, $0.02 cost)
- **Quality**: ValidationAgent checks completeness, quality, consistency
- **Monitoring**: Real-time progress tracking with cost estimation
- **Consolidation**: Duplicate detection (fuzzy + semantic), entity merging, relationship discovery
- **Fallback**: 6-model chain (gpt-4o-mini → gpt-4o → gpt-3.5-turbo → o1-mini → o1-preview → claude-3.5-sonnet)
- **Rate Limiting**: 50 calls/minute to prevent API failures
- **Resume**: Can resume interrupted extractions

### Current Gaps

- No prompt versioning system
- No quantitative evaluation pipeline (30-sample test set planned)
- No PII detection guardrails
- No caching layer
- No user feedback loop
- No hard cost limits (only estimation + confirmation)
- Parallel processing broken (SQLite WAL mode issues)

---

## Your Task

Create a **complete requirements document** following these strict rules:

### EARS Patterns (MANDATORY)

Every requirement MUST use exactly one of these patterns:

1. **Ubiquitous**: THE <system> SHALL <response>
2. **Event-driven**: WHEN <trigger>, THE <system> SHALL <response>
3. **State-driven**: WHILE <condition>, THE <system> SHALL <response>
4. **Unwanted event**: IF <condition>, THEN THE <system> SHALL <response>
5. **Optional feature**: WHERE <option>, THE <system> SHALL <response>
6. **Complex**: [WHERE] [WHILE] [WHEN/IF] THE <system> SHALL <response> (in this order)

### INCOSE Quality Rules (MANDATORY)

- ✅ Active voice (who does what)
- ✅ No vague terms ("quickly", "adequate", "reasonable")
- ✅ No escape clauses ("where possible", "if feasible")
- ✅ No negative statements ("SHALL not...")
- ✅ One thought per requirement
- ✅ Explicit and measurable conditions
- ✅ Consistent terminology (use glossary)
- ✅ No pronouns ("it", "them")
- ✅ No absolutes ("never", "always", "100%")
- ✅ Solution-free (focus on what, not how)
- ✅ Realistic tolerances

### Document Structure (MANDATORY)

```markdown
# Requirements Document

## Introduction
[2-3 paragraph summary of system0 and its purpose]

## Glossary
- **System0**: [Definition]
- **Entity**: [Definition]
- **Extraction**: [Definition]
- **Interview**: [Definition]
- **Validation**: [Definition]
- **Consolidation**: [Definition]
- [Add all technical terms used in requirements]

## Requirements

### Requirement 1: Core Extraction Capability

**User Story:** As a business analyst, I want system0 to extract structured entities from Spanish interviews, so that I can analyze business intelligence without manual transcription.

#### Acceptance Criteria

1. WHEN System0 receives a Spanish interview transcript, THE System SHALL extract entities for all 17 entity types within 30 seconds.

2. THE System SHALL achieve entity extraction accuracy of at least 85 percent for pain points, processes, and systems.

3. IF extraction accuracy falls below 85 percent, THEN THE System SHALL flag the interview for manual review.

4. THE System SHALL preserve Spanish language content without translation during extraction.

5. THE System SHALL encode all extracted text using UTF-8 with ensure_ascii set to False.

[Continue with more acceptance criteria...]

### Requirement 2: Quality Validation

**User Story:** As a data quality manager, I want system0 to validate extraction quality automatically, so that I can trust the extracted data without manual verification.

#### Acceptance Criteria

1. THE System SHALL check completeness of extracted entities against interview content.

2. WHEN ValidationAgent detects missing entities, THE System SHALL report which entity types are incomplete.

3. THE System SHALL validate quality of extracted entities for UTF-8 encoding correctness.

4. THE System SHALL check consistency of entity references across all extracted entities.

5. IF quality validation detects errors, THEN THE System SHALL mark affected entities with validation_failed flag.

[Continue with more acceptance criteria...]

### Requirement 3: Cost Control

**User Story:** As a project manager, I want system0 to control API costs, so that I can stay within budget constraints.

#### Acceptance Criteria

1. THE System SHALL estimate API cost before processing interviews.

2. WHEN estimated cost exceeds 1 dollar, THE System SHALL require user confirmation before proceeding.

3. THE System SHALL enforce a hard limit of 1000 dollars per month for API costs.

4. IF monthly cost reaches 900 dollars, THEN THE System SHALL send a warning alert.

5. IF monthly cost reaches 1000 dollars, THEN THE System SHALL stop processing and require approval.

[Continue with more acceptance criteria...]

### Requirement 4: Failure Handling

**User Story:** As a system operator, I want system0 to handle API failures gracefully, so that extractions can complete successfully despite transient errors.

#### Acceptance Criteria

1. WHEN an API call fails with rate limit error, THE System SHALL retry with exponential backoff up to 3 times.

2. IF primary model fails after 3 retries, THEN THE System SHALL fallback to next model in chain.

3. THE System SHALL support 6 models in fallback chain: gpt-4o-mini, gpt-4o, gpt-3.5-turbo, o1-mini, o1-preview, claude-3-5-sonnet.

4. IF all models fail after all retries, THEN THE System SHALL log error and mark interview as failed.

5. THE System SHALL allow resuming failed extractions without reprocessing completed interviews.

[Continue with more acceptance criteria...]

### Requirement 5: Performance

**User Story:** As a business analyst, I want system0 to process interviews quickly, so that I can get insights in a timely manner.

#### Acceptance Criteria

1. THE System SHALL process a single interview in less than 30 seconds on average.

2. THE System SHALL process 44 interviews in less than 20 minutes.

3. THE System SHALL limit API calls to 50 per minute to prevent rate limiting.

4. THE System SHALL track processing time per interview and report in monitoring dashboard.

5. WHERE caching is enabled, THE System SHALL reduce processing time by at least 50 percent for repeated interviews.

[Continue with more acceptance criteria...]

### Requirement 6: Security and Privacy

**User Story:** As a compliance officer, I want system0 to protect sensitive information, so that we comply with data protection regulations.

#### Acceptance Criteria

1. THE System SHALL detect personally identifiable information in interview transcripts.

2. WHEN PII is detected, THE System SHALL redact or anonymize the information before storage.

3. THE System SHALL prevent SQL injection attacks by using parameterized queries for all database operations.

4. THE System SHALL log all data access operations with timestamp and user identifier.

5. THE System SHALL encrypt sensitive data at rest in the database.

[Continue with more acceptance criteria...]

### Requirement 7: Monitoring and Observability

**User Story:** As a system operator, I want system0 to provide real-time monitoring, so that I can detect and resolve issues quickly.

#### Acceptance Criteria

1. THE System SHALL track extraction progress in real-time with ExtractionMonitor.

2. THE System SHALL report entity counts per type for each processed interview.

3. THE System SHALL calculate and display cumulative cost during extraction runs.

4. THE System SHALL log all errors with interview ID, entity type, and error message.

5. WHEN extraction completes, THE System SHALL generate a summary report with success rate, error count, and total cost.

[Continue with more acceptance criteria...]

### Requirement 8: Prompt Engineering

**User Story:** As an AI engineer, I want system0 to support prompt versioning, so that I can improve extraction quality iteratively.

#### Acceptance Criteria

1. THE System SHALL store prompts in a prompts directory with version numbers.

2. THE System SHALL support at least 3 prompt versions: v1_basic, v2_structured, v3_examples.

3. THE System SHALL allow selecting active prompt version via configuration file.

4. THE System SHALL track which prompt version was used for each extraction.

5. THE System SHALL support A/B testing by processing same interview with multiple prompt versions.

[Continue with more acceptance criteria...]

### Requirement 9: Evaluation Pipeline

**User Story:** As a data scientist, I want system0 to evaluate extraction accuracy, so that I can measure and improve quality over time.

#### Acceptance Criteria

1. THE System SHALL maintain a test set of 30 labeled interviews with ground truth entities.

2. THE System SHALL calculate entity extraction accuracy as true positives divided by sum of true positives, false positives, and false negatives.

3. THE System SHALL calculate sentiment F1 score for sentiment-bearing entities.

4. THE System SHALL calculate fact completeness as percentage of ground truth facts extracted.

5. THE System SHALL generate evaluation report comparing accuracy across prompt versions.

[Continue with more acceptance criteria...]

### Requirement 10: User Feedback Loop

**User Story:** As a business analyst, I want to rate extraction quality, so that system0 can learn from my feedback and improve over time.

#### Acceptance Criteria

1. THE System SHALL provide a 5-star rating interface for each extracted interview.

2. THE System SHALL allow users to flag incorrect entities for correction.

3. THE System SHALL store user corrections in a feedback database.

4. THE System SHALL use feedback data to retrain or fine-tune extraction models.

5. THE System SHALL track average user rating per prompt version.

[Continue with more acceptance criteria...]

[Add more requirements as needed for:]
- Requirement 11: Knowledge Graph Consolidation
- Requirement 12: RAG 2.0 Integration
- Requirement 13: Caching and Performance Optimization
- Requirement 14: Deployment and Operations
- Requirement 15: Documentation and Training
```

---

## Specific Requirements to Include

### Functional Requirements

1. **Core Extraction** (10-15 acceptance criteria)
   - 17 entity types
   - Spanish language processing
   - UTF-8 encoding
   - Processing time <30s
   - Accuracy ≥85%

2. **Quality Validation** (8-12 acceptance criteria)
   - Completeness checking
   - Quality validation
   - Consistency checking
   - Hallucination detection

3. **Cost Control** (5-8 acceptance criteria)
   - Cost estimation
   - User confirmation
   - Hard limits ($1000/month)
   - Alerts at 90% threshold

4. **Failure Handling** (8-10 acceptance criteria)
   - Retry logic (3 attempts)
   - Exponential backoff
   - Multi-model fallback (6 models)
   - Resume capability

5. **Prompt Engineering** (6-8 acceptance criteria)
   - Version control (v1, v2, v3)
   - A/B testing
   - Evaluation pipeline
   - 30-sample test set

6. **User Feedback** (5-7 acceptance criteria)
   - 5-star rating system
   - Correction mechanism
   - Feedback storage
   - Continuous improvement

### Non-Functional Requirements

7. **Performance** (6-8 acceptance criteria)
   - Processing time <30s per interview
   - Rate limiting (50 calls/min)
   - Caching (50% speedup)
   - Batch processing (44 interviews <20 min)

8. **Security** (8-10 acceptance criteria)
   - PII detection
   - Data encryption
   - SQL injection prevention
   - Audit logging
   - Access control

9. **Monitoring** (6-8 acceptance criteria)
   - Real-time progress tracking
   - Cost tracking
   - Error logging
   - Summary reports
   - Alerting

10. **Reliability** (8-10 acceptance criteria)
    - 99.9% uptime
    - Graceful degradation
    - Circuit breaker
    - Health checks
    - Rollback capability

### Operational Requirements

11. **Deployment** (5-7 acceptance criteria)
    - Environment configuration
    - Database migrations
    - Dependency management
    - Version control
    - Rollback procedures

12. **Documentation** (4-6 acceptance criteria)
    - API documentation
    - User guides
    - Runbooks
    - Architecture diagrams
    - Code comments

---

## Quality Checklist

Before submitting the requirements document, verify:

### EARS Compliance
- [ ] Every requirement uses exactly one EARS pattern
- [ ] Complex requirements follow WHERE → WHILE → WHEN/IF → THE → SHALL order
- [ ] All system names are defined in glossary
- [ ] No requirements use "SHALL not" (use positive statements)

### INCOSE Quality
- [ ] All requirements use active voice
- [ ] No vague terms (quickly, adequate, reasonable)
- [ ] No escape clauses (where possible, if feasible)
- [ ] One thought per requirement
- [ ] All conditions are explicit and measurable
- [ ] Consistent terminology throughout
- [ ] No pronouns (it, them, they)
- [ ] No absolutes (never, always, 100%)
- [ ] Solution-free (what, not how)
- [ ] Realistic tolerances

### Testability
- [ ] Every requirement has measurable acceptance criteria
- [ ] Quantitative thresholds specified (≥85%, <30s, etc.)
- [ ] Test methods are clear
- [ ] Success criteria are unambiguous

### Completeness
- [ ] All functional requirements covered
- [ ] All non-functional requirements covered
- [ ] All operational requirements covered
- [ ] All failure modes addressed
- [ ] All security concerns addressed

---

## Example of Excellent Requirement

**User Story:** As a business analyst, I want system0 to extract pain points accurately, so that I can identify business problems without manual review.

#### Acceptance Criteria

1. WHEN System0 receives an interview transcript containing pain point keywords, THE System SHALL extract at least 85 percent of pain points mentioned in the transcript.

2. THE System SHALL classify each pain point into one of 7 categories: Process, Data, Systems, Culture, Training, Approval, or Integration.

3. THE System SHALL assign severity level to each pain point: Low, Medium, High, or Critical.

4. THE System SHALL identify affected roles for each pain point with at least 80 percent accuracy.

5. IF a pain point description contains fewer than 10 words, THEN THE System SHALL flag it for manual review.

6. THE System SHALL preserve Spanish language content in pain point descriptions without translation.

7. WHEN ValidationAgent detects missing pain points, THE System SHALL report the count of missing pain points and suggest re-extraction.

---

## Output Format

Provide the complete requirements document in Markdown format, ready to replace `.kiro/specs/zero-ai/requirements.md`.

Include:
1. Introduction (2-3 paragraphs)
2. Glossary (all technical terms)
3. At least 12 requirements with user stories
4. At least 80 total acceptance criteria
5. All requirements EARS-compliant
6. All requirements INCOSE-compliant

---

## Additional Context

### Current System Metrics (from codebase)
- **Extraction time:** ~30s per interview
- **Cost:** ~$0.02 per interview
- **Entity types:** 17 (6 v1.0 + 11 v2.0)
- **Models:** 6 in fallback chain
- **Rate limit:** 50 calls/minute
- **Database:** SQLite with WAL mode
- **Consolidation:** 77% complete (40/52 tasks)
- **RAG 2.0:** In progress (Week 1/5)

### Target Metrics (from enhancement plan)
- **Entity Extraction Accuracy:** ≥85%
- **Sentiment F1 Score:** ≥80%
- **Fact Completeness:** ≥75%
- **Processing Time:** <30s per interview
- **Cost:** <$0.03 per interview
- **Monthly Budget:** $500-$1000
- **Uptime:** 99.9%
- **User Rating:** ≥4.5/5

### Spanish Language Requirements
- **Encoding:** UTF-8 with ensure_ascii=False
- **No Translation:** All content must remain in Spanish
- **Stopwords:** Spanish stopwords for chunking
- **Stemming:** Spanish stemming for similarity
- **Cultural Context:** Latin American business terminology

---

## Begin Generation

Please generate the complete EARS-compliant requirements document now, following all rules and guidelines above.

# Requirements Document: Enhanced Ontology Schema for Knowledge Graph

## Introduction

This document defines requirements for enhancing the current ontology schema (v1.0) to support AI-driven transformation across a holding company with three subsidiaries and their business units:

- **Hotel Los Tajibos**: Hospitality (rooms), Food & Beverage (buffet, restaurants, bars), Events & Catering
- **Comversa**: Construction, Real Estate Management, Real Estate Investment, Building Maintenance
- **Bolivian Foods**: Manufacturing, Franchise Operations, Distribution

The enhanced schema must:
1. Enable **data-driven validation** of CEO assumptions about process priorities (RECALIBRACIÓN FASE 1) vs discovering new automation opportunities
2. Support **multi-level hierarchy**: Holding → Company → Business Unit → Department → Process
3. Create **separate RAG databases per company** that can be queried independently or aggregated at holding level
4. Capture not only WHAT processes exist and WHAT problems occur, but also HOW work gets done, WHEN actions happen, WHO makes decisions, WHERE data flows, and WHY failures occur

This operational intelligence is critical for AI agents to route requests, escalate issues, predict failures, and coordinate across teams.

## Glossary

- **Ontology Schema**: Structured data model defining entities, attributes, and relationships for knowledge graph
- **Knowledge Graph**: Graph database storing interconnected business intelligence from interviews
- **RAG Database**: Retrieval-Augmented Generation database enabling AI agents to query company-specific knowledge
- **Holding**: Parent company (Comversa Group) owning three subsidiary companies
- **Company**: Subsidiary business entity (Hotel Los Tajibos, Comversa, Bolivian Foods)
- **Business Unit**: Operational division within a company (e.g., F&B, Construction, Franchises)
- **Pain Point**: Specific problem, bottleneck, or inefficiency identified in business operations
- **AI Agent**: Autonomous software system that takes actions based on knowledge graph data
- **Service Design Research**: Systematic analysis of customer/employee experiences to identify improvement opportunities
- **Jobs-To-Be-Done (JTBD)**: Framework focusing on what users are trying to accomplish rather than features
- **Hair-on-Fire Problem**: Critical issue with high intensity (8-10/10) and high frequency (daily/weekly)
- **Macroproceso**: High-level business process spanning multiple departments (13 identified in RECALIBRACIÓN FASE 1)
- **Microproceso**: Detailed subprocess or task within a macroproceso (15-20 identified)
- **Quick Win**: Low effort, high impact automation opportunity (Quadrant 1 in Effort vs Impact matrix)
- **Extraction System**: LLM-based system that processes interview transcripts to populate knowledge graph
- **WhatsApp Diagnostic**: Interview methodology using WhatsApp for rapid qualitative data collection (44 interviews conducted)
- **CEO Assumptions**: Prioritized macroprocesos from RECALIBRACIÓN FASE 1 requiring data validation

## Requirements

### Requirement 1: Pain Point Intensity & Frequency Scoring

**User Story:** As a Digital Transformation Officer, I want pain points scored by intensity and frequency, so that I can prioritize "hair-on-fire" problems that deliver maximum ROI.

#### Acceptance Criteria

1. WHEN the Extraction System processes an interview transcript, THE System SHALL extract pain point intensity on a scale of 1-10 based on language indicators (e.g., "crítico", "urgente", "bloqueante" = 8-10)

2. WHEN the Extraction System identifies a pain point, THE System SHALL classify frequency as one of: ["Daily", "Weekly", "Monthly", "Quarterly", "Annually", "Ad-hoc"]

3. WHEN a pain point has intensity >= 8 AND frequency in ["Daily", "Weekly"], THE System SHALL flag it as "hair_on_fire" = true

4. WHEN storing pain points in the Knowledge Graph, THE System SHALL include fields: intensity_score, frequency, hair_on_fire, estimated_time_wasted_per_occurrence

5. WHERE a pain point mentions cost impact (e.g., "perdemos $X", "cuesta Y horas"), THE System SHALL extract and store cost_impact_monthly in USD

### Requirement 2: Jobs-To-Be-Done Context Mapping

**User Story:** As a Service Design Analyst, I want pain points mapped to Jobs-To-Be-Done context (WHO, WHAT, WHERE), so that I understand the full situational context for each problem.

#### Acceptance Criteria

1. WHEN the Extraction System identifies a pain point, THE System SHALL extract WHO is affected (specific roles, not generic terms like "equipo")

2. WHEN storing a pain point, THE System SHALL capture WHAT job the person is trying to accomplish when the pain occurs

3. WHEN a pain point is mentioned, THE System SHALL identify WHERE in the business process it occurs (e.g., "durante cierre mensual", "al recibir solicitud")

4. WHEN multiple roles are affected by the same pain point, THE System SHALL create separate pain_point entries with role-specific context

5. THE System SHALL store pain points using JTBD language format: "When [situation], I want to [motivation], but [obstacle]"

### Requirement 3: Communication Channel Intelligence

**User Story:** As an AI Agent Developer, I want to know HOW people communicate for each process, so that AI agents can route messages through the correct channels with appropriate SLAs.

#### Acceptance Criteria

1. WHEN the Extraction System identifies a process mention, THE System SHALL extract all communication channels used (e.g., "WhatsApp", "Outlook", "reuniones semanales")

2. WHEN a communication channel is mentioned, THE System SHALL capture its purpose (e.g., "urgencias", "solicitudes formales", "coordinación diaria")

3. WHERE response time expectations are mentioned (e.g., "inmediato", "mismo día"), THE System SHALL extract and normalize to response_sla_minutes

4. WHEN storing communication channels, THE System SHALL link them to specific processes and capture pain_points (e.g., "pérdida de trazabilidad", "información dispersa")

5. THE System SHALL create a CommunicationChannel entity with fields: channel_name, purpose, frequency, participants, response_sla_minutes, pain_points

### Requirement 4: Decision Point & Escalation Logic

**User Story:** As an AI Agent, I want to know WHO makes decisions and WHEN to escalate, so that I can route requests to the correct person based on priority criteria.

#### Acceptance Criteria

1. WHEN the Extraction System identifies decision-making language (e.g., "yo decido", "requiere aprobación de", "escalo a"), THE System SHALL create a DecisionPoint entity

2. WHEN a decision point is captured, THE System SHALL extract decision_criteria as a list of conditions (e.g., ["Afecta seguridad", "Monto > $X", "Impacta ventas"])

3. WHEN escalation triggers are mentioned, THE System SHALL capture escalation_trigger and escalation_to_role

4. THE System SHALL store decision_maker_role, decision_type, approval_required (boolean), and approval_threshold (if applicable)

5. WHERE decision authority limits are mentioned (e.g., "hasta $5000 puedo aprobar"), THE System SHALL extract and store authority_limit_usd

### Requirement 5: Data Flow & System Integration Mapping

**User Story:** As a System Architect, I want to know WHERE data lives and HOW it moves between systems, so that I can design integrations and identify data quality issues.

#### Acceptance Criteria

1. WHEN the Extraction System identifies data movement language (e.g., "paso datos de X a Y", "concilio entre", "doble entrada"), THE System SHALL create a DataFlow entity

2. WHEN a data flow is captured, THE System SHALL extract source_system, target_system, data_type, and transfer_method (e.g., "Manual", "API", "Export/Import")

3. WHEN data quality issues are mentioned (e.g., "errores de conciliación", "datos inconsistentes"), THE System SHALL capture data_quality_issues

4. THE System SHALL store transfer_frequency (e.g., "Hourly", "Daily", "Weekly") and pain_points related to the data flow

5. WHERE integration pain points are mentioned, THE System SHALL link them to both the DataFlow entity and the related System entities

### Requirement 6: Temporal Pattern Recognition

**User Story:** As an AI Agent, I want to know WHEN activities happen (time of day, frequency, duration), so that I can schedule actions at optimal times and predict workload patterns.

#### Acceptance Criteria

1. WHEN the Extraction System identifies temporal language (e.g., "diario a las 9am", "cada lunes", "cierre mensual"), THE System SHALL create a TemporalPattern entity

2. WHEN a temporal pattern is captured, THE System SHALL normalize frequency to standard values: ["Hourly", "Daily", "Weekly", "Monthly", "Quarterly", "Annually"]

3. WHERE specific times are mentioned, THE System SHALL extract time_of_day in 24-hour format (e.g., "09:00")

4. THE System SHALL capture duration_minutes if mentioned (e.g., "reunión de 30 minutos")

5. WHEN temporal patterns trigger actions, THE System SHALL link to related processes and capture triggers_actions as a list

### Requirement 7: Failure Mode & Recovery Documentation

**User Story:** As an Operations Manager, I want to know WHAT goes wrong, HOW OFTEN, and WHAT workarounds exist, so that I can design preventive measures and improve resilience.

#### Acceptance Criteria

1. WHEN the Extraction System identifies failure language (e.g., "se cae", "falla", "no funciona", "problema recurrente"), THE System SHALL create a FailureMode entity

2. WHEN a failure mode is captured, THE System SHALL extract failure_description, frequency, impact_description, and current_workaround

3. WHERE root causes are mentioned or implied, THE System SHALL capture root_cause

4. THE System SHALL store recovery_time_minutes if mentioned (e.g., "tarda 2 horas en resolverse")

5. WHEN preventive solutions are suggested, THE System SHALL capture proposed_prevention and link to related AutomationCandidate entities

### Requirement 8: Enhanced Process Entity with Operational Context

**User Story:** As a Process Analyst, I want processes enriched with communication methods, decision points, failure modes, and temporal patterns, so that I have complete operational context.

#### Acceptance Criteria

1. WHEN the Extraction System creates a Process entity, THE System SHALL link it to related CommunicationChannel entities

2. WHEN a process is stored, THE System SHALL link it to related DecisionPoint entities

3. THE System SHALL link processes to related FailureMode entities

4. THE System SHALL link processes to related TemporalPattern entities

5. THE System SHALL enhance the Process entity with fields: communication_methods (list), decision_points (list), failure_modes (list), temporal_patterns (list)

### Requirement 9: Enhanced PainPoint Entity with Root Cause & Cost

**User Story:** As a Business Analyst, I want pain points enriched with root causes, workarounds, and quantified costs, so that I can calculate ROI for automation initiatives.

#### Acceptance Criteria

1. WHEN the Extraction System creates a PainPoint entity, THE System SHALL attempt to extract or infer root_cause

2. WHEN a pain point is stored, THE System SHALL capture current_workaround if mentioned

3. WHERE cost impact is mentioned, THE System SHALL extract cost_impact_monthly_usd

4. THE System SHALL capture time_wasted_per_occurrence_minutes if mentioned or estimable

5. THE System SHALL calculate estimated_annual_cost_usd = (time_wasted_per_occurrence_minutes * frequency_per_year * hourly_rate) + cost_impact_monthly_usd * 12

### Requirement 10: Enhanced System Entity with Integration & Satisfaction Data

**User Story:** As a Technology Manager, I want systems enriched with integration pain points, data quality issues, and user satisfaction, so that I can prioritize system replacements or improvements.

#### Acceptance Criteria

1. WHEN the Extraction System updates a System entity, THE System SHALL capture integration_pain_points as a list

2. WHEN data quality issues are mentioned for a system, THE System SHALL store data_quality_issues

3. WHERE user sentiment is expressed (e.g., "me gusta", "es complicado", "no sirve"), THE System SHALL infer user_satisfaction_score (1-10)

4. THE System SHALL flag replacement_candidate = true if negative sentiment is strong (score <= 3) or if replacement is explicitly mentioned

5. THE System SHALL track adoption_rate if mentioned (e.g., "solo 30% del equipo lo usa")

### Requirement 11: Enhanced AutomationCandidate with Monitoring & Approval

**User Story:** As an Automation Engineer, I want automation candidates enriched with current workarounds, data sources needed, and approval requirements, so that I can design complete automation solutions.

#### Acceptance Criteria

1. WHEN the Extraction System creates an AutomationCandidate entity, THE System SHALL capture current_manual_process_description

2. WHEN an automation is identified, THE System SHALL list data_sources_needed (systems that must be integrated)

3. THE System SHALL determine approval_required (boolean) based on decision point analysis

4. WHERE monitoring needs are mentioned or implied, THE System SHALL capture monitoring_metrics as a list

5. THE System SHALL link to related FailureMode entities to inform error handling design

### Requirement 12: Extraction Quality & Validation

**User Story:** As a Data Quality Manager, I want extraction confidence scores and validation flags, so that I can review low-confidence extractions and ensure data accuracy.

#### Acceptance Criteria

1. WHEN the Extraction System creates any entity, THE System SHALL assign a confidence_score (0.0-1.0) based on language clarity and context

2. WHEN confidence_score < 0.7, THE System SHALL flag needs_review = true

3. THE System SHALL log extraction_source (interview_id, question_number) for traceability

4. WHEN contradictory information is detected across interviews, THE System SHALL flag conflict = true and store conflicting_sources

5. THE System SHALL provide extraction_reasoning (brief explanation of why entity was extracted) for transparency

### Requirement 13: Cross-Company Pattern Recognition

**User Story:** As a Digital Transformation Officer, I want to identify patterns across all three companies, so that I can design shared solutions and leverage economies of scale.

#### Acceptance Criteria

1. WHEN the Extraction System processes interviews from multiple companies, THE System SHALL identify common pain points across companies

2. WHEN a process exists in multiple companies with different implementations, THE System SHALL flag standardization_opportunity = true

3. THE System SHALL calculate pain_point_prevalence = count of companies affected / total companies

4. WHERE the same system is used across companies with different pain points, THE System SHALL aggregate and compare pain_points by company

5. THE System SHALL generate cross_company_insights highlighting shared challenges and divergent approaches

### Requirement 14: Priority Matrix Integration

**User Story:** As a Project Manager, I want automation candidates automatically mapped to the Effort vs Impact matrix, so that I can identify Quick Wins and Strategic initiatives.

#### Acceptance Criteria

1. WHEN the Extraction System creates an AutomationCandidate, THE System SHALL estimate effort_score (1-5) based on complexity and systems_involved

2. WHEN an automation candidate is stored, THE System SHALL estimate impact_score (1-5) based on pain point severity, frequency, and affected_roles count

3. THE System SHALL assign priority_quadrant based on effort and impact: ["Quick Win", "Strategic", "Incremental", "Reconsider"]

4. WHERE ROI can be calculated (cost savings / implementation cost), THE System SHALL store estimated_roi_months

5. THE System SHALL rank automation candidates within each quadrant by ROI or impact score

### Requirement 15: Multi-Level Organizational Hierarchy

**User Story:** As a Digital Transformation Officer, I want entities organized by Holding → Company → Business Unit → Department, so that I can query data at any level and create company-specific RAG databases.

#### Acceptance Criteria

1. WHEN the Extraction System processes an interview, THE System SHALL identify and store: holding_name, company_name, business_unit, department

2. WHEN a company is "Hotel Los Tajibos", THE System SHALL classify business_unit as one of: ["Hospitality", "Food & Beverage", "Events & Catering", "Shared Services"]

3. WHEN a company is "Comversa", THE System SHALL classify business_unit as one of: ["Construction", "Real Estate Management", "Real Estate Investment", "Building Maintenance", "Corporate"]

4. WHEN a company is "Bolivian Foods", THE System SHALL classify business_unit as one of: ["Manufacturing", "Franchise Operations", "Distribution", "Corporate"]

5. THE System SHALL enable filtering of all entities by company_name and business_unit for RAG database segmentation

### Requirement 16: CEO Assumption Validation Framework

**User Story:** As a Digital Transformation Officer, I want to validate CEO-prioritized macroprocesos against interview data, so that I can confirm assumptions or discover overlooked opportunities.

#### Acceptance Criteria

1. WHEN the Extraction System identifies a process matching a CEO-prioritized macroproceso (from RECALIBRACIÓN FASE 1), THE System SHALL flag ceo_priority = true and store priority_quadrant

2. WHEN pain points are extracted, THE System SHALL calculate data_support_score = (count of interviews mentioning this pain / total interviews) to validate CEO assumptions

3. WHERE a high-frequency pain point (mentioned in >= 30% of interviews) is NOT in CEO priorities, THE System SHALL flag overlooked_opportunity = true

4. THE System SHALL generate a validation_report comparing CEO-prioritized macroprocesos vs data-driven pain point frequency

5. WHEN automation candidates are identified that don't map to CEO priorities, THE System SHALL flag emergent_opportunity = true and calculate potential_roi

### Requirement 17: Company-Specific RAG Database Architecture

**User Story:** As an AI Engineer, I want separate RAG databases per company with a unified schema, so that AI agents can query company-specific knowledge or aggregate across the holding.

#### Acceptance Criteria

1. WHEN storing entities in the Knowledge Graph, THE System SHALL partition data by company_name to enable separate RAG database creation

2. THE System SHALL maintain a unified schema across all company RAG databases for cross-company queries

3. WHEN querying the Knowledge Graph, THE System SHALL support filters: company_name, business_unit, department, date_range

4. THE System SHALL enable aggregation queries across companies (e.g., "Show all pain points related to inventory management across all companies")

5. THE System SHALL generate company-specific embeddings for RAG retrieval while maintaining holding-level embeddings for cross-company insights

### Requirement 18: Business Unit Context Enrichment

**User Story:** As a Business Analyst, I want processes and pain points enriched with business unit context, so that I understand industry-specific challenges (hospitality vs construction vs manufacturing).

#### Acceptance Criteria

1. WHEN the Extraction System identifies a process in "Food & Beverage" business unit, THE System SHALL tag with industry_context = "Hospitality"

2. WHEN a process is in "Construction" or "Real Estate" business units, THE System SHALL tag with industry_context = "Real Estate & Construction"

3. WHEN a process is in "Manufacturing" or "Franchise Operations", THE System SHALL tag with industry_context = "Food Manufacturing & Retail"

4. THE System SHALL capture business_unit_specific_kpis (e.g., "Occupancy Rate" for Hospitality, "Cost per Square Meter" for Construction)

5. WHERE pain points are common across business units but with different root causes, THE System SHALL create separate PainPoint entities with business_unit_context

### Requirement 19: Interview Metadata & Traceability

**User Story:** As a Research Analyst, I want complete interview metadata and traceability, so that I can validate findings and conduct follow-up research.

#### Acceptance Criteria

1. WHEN the Extraction System processes an interview, THE System SHALL capture interview_date, company, business_unit, respondent_name, respondent_role, department

2. THE System SHALL store interview_duration_minutes and interview_method (e.g., "WhatsApp", "Video call", "In-person")

3. WHEN any entity is extracted, THE System SHALL link it to the source interview via interview_id

4. THE System SHALL preserve raw_qa_pairs in the Interview entity for future re-processing

5. WHERE follow-up questions are needed, THE System SHALL generate suggested_follow_up_questions based on gaps or ambiguities

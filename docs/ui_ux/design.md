# Grupo Conversa Intelligence – UX/UI Proposal

## 1. Purpose & Scope

Create a cohesive front-end experience that surfaces the intelligence gathered across the 17-entity ontology before the RAG 2.0 rollout. The proposal focuses on three interaction surfaces already proved valuable during discovery:

1. **Operations Dashboard** – monitors extraction coverage, consolidation quality, and intelligence health.
2. **Deliverable Studio** – leverages AI agents to package insights (process docs, priority matrices, dashboard specs).
3. **Ontology & Governance Console** – manages organizational hierarchies, contradictions, and approval workflows.

This design file aligns engineering, design, and product so we can decompose subsequent tasks with clarity.

## 2. Personas & User Goals

| Persona | Primary Goals | Key Needs |
| --- | --- | --- |
| **Data Steward** | Validate duplicate merges, triage contradictions, track consolidation metrics | Evidence for merge decisions, fast filters, Spanish copy |
| **Transformation Consultant** | Synthesize insights into deliverables for leadership | Curatable templates, agent guardrails, export options |
| **PMO / Operations Exec** | Monitor top pain points, automation pipeline, and KPIs | Quick read dashboards, drill-down to interviews, alerts |
| **Ontology Architect** | Maintain holding → company → BU → department schema | Visual tree diff, approval queue, change history |

## 3. Experience Architecture

```
Sidebar Navigation
│
├─ Dashboard (Operations Exec)
│   ├─ Intelligence KPIs (interviews processed, coverage, consensus score)
│   ├─ Priority Spotlight (pain points + automation wins)
│   └─ Quality Alerts (contradictions, encoding issues, SLAs)
│
├─ Deliverable Studio (Consultant)
│   ├─ Template Picker
│   ├─ Context Config (filters, data snippets)
│   └─ Agent Output + Export pane
│
└─ Ontology Console (Data Steward / Architect)
    ├─ Org Tree & Deviations
    ├─ Relationship Explorer
    └─ Approval queue & audit log
```

Back-end touchpoints per section:

- **Dashboard**: `interviews`, `pain_points`, `automation_candidates`, `patterns`, `consolidation_audit`. Requires summary endpoints + health metrics.
- **Deliverable Studio**: Read-only queries on `processes`, `kpis`, `pain_points`, `automation_candidates`; POST to `/agents/deliverables` for Claude runs.
- **Ontology Console**: `hierarchy_discoverer` outputs, `relationships`, `contradictions`, `ontology_proposals`.

## 4. Detailed UX Concepts

### 4.1 Operations Dashboard
- **Hero KPI Row**: interviews processed, duplicate reduction %, consensus confidence average, number of new contradictions.
- **Charts**:
  - Timeline of extraction & consolidation throughput (line chart).
  - Impact vs effort quadrant showing automation candidates (scatter).
  - Top recurring pain points with frequency (bar).
- **Alerts Panel**: cards for “Encoding issues”, “Low-confidence entities”, “Pending ontology approvals”.
- **Interactions**: time range filters, company drop-down, click-through to detail modals.

### 4.2 Deliverable Studio
- **Template Picker**: Process Doc, Priority Matrix, Dashboard Spec (extensible).
- **Context Builder**:
  - Data filters (company, department, entity type).
  - Preview tables (up to 10 rows) with copy-to-clipboard.
  - Editable brief to nudge the agent (e.g., focus question).
- **Agent Pane**:
  - Run button stateful (loading, success, retry).
  - Rich-text display + Markdown download.
  - Token/cost estimate badge from CostGuard.
- **Safeguards**: disable run when Anthropic key absent; show Spanish warnings for missing context.

### 4.3 Ontology & Governance Console
- **Hierarchy Explorer**:
  - Tree view with badges for “confirmed”, “new discovery”, “needs alias”.
  - Split pane showing “Predefinido vs Detectado” for selected node.
- **Approval Queue**:
  - Table of pending proposals with evidence count, confidence, interviews.
  - Actions: aprobar, rechazar, solicitar cambios.
  - Audit trail modal referencing `consolidation_audit`.
- **Relationship Explorer**:
  - Graph mini-view (departments ↔ processes ↔ systems) with filters.
  - Table view listing relationship type, confidence, supporting interviews.

## 5. Information Architecture & Data Requirements

| Section | Data Needed | Source / API |
| --- | --- | --- |
| KPI Row | counts, consensus stats, duplicate reduction | `/metrics/summary`, `/consolidation/stats` |
| Pain/Automation charts | aggregated frequency & impact scores | `/pain-points/summary`, `/automation/summary` |
| Alerts | contradictions, encoding issues, SLA breaches | `/quality/issues`, `/ontology/deviations` |
| Deliverable context | filtered entities, optional CSV exports | `/processes`, `/pain-points`, `/automation` (with filters) |
| Agent runs | asynchronous job + CostGuard log | `/agents/deliverables` (POST), `/agents/jobs/{id}` |
| Ontology tree | current schema vs discovered nodes | `/ontology/tree`, `/ontology/deviations` |
| Approvals | queue, audit log, change history | `/ontology/proposals`, `/ontology/audit` |
| Relationships | nodes + edges + evidence | `/relationships/search`, `/relationships/evidence` |

## 6. UI System & Component Library

- **Framework**: Next.js 14 + TypeScript + Tailwind (production path). Streamlit remains for prototyping.
- **Components**:
  - `MetricCard`, `ChartCard`, `AlertBanner`.
  - `DataTable` with CSV export.
  - `AgentRunPanel` (input form + output viewer + download).
  - `OrgTree` (virtualized tree with status chips).
  - `RelationshipGraph` (Cytoscape/Reaflow embedding).
- **Internationalization**: Spanish default; ensure numeral / date formats respect ES locale.
- **Accessibility**: high-contrast mode, keyboard navigation for tree + tables.

## 7. Implementation Roadmap

1. **Prototype Hardening (Week 0-1)**
   - Finalize Streamlit proof (done) and add logging hooks for user flows.
   - Define REST contracts and stub FastAPI endpoints for metrics, deliverables, ontology.

2. **Next.js Foundation (Week 2)**
   - Bootstrap project with shared auth/layout, hook into metrics APIs.
   - Implement hero KPI row + chart placeholders fed by mocked data.

3. **Deliverable Studio (Week 3)**
   - Build template picker & context builder.
   - Integrate Anthropic job service with retry + status polling.

4. **Ontology Console (Week 4)**
   - Ship tree explorer + approval queue with real data.
   - Add relationship explorer with simple filters.

5. **Quality & Alerts (Week 5)**
   - Wire consolidation + QA alerts, run usability review.
   - Add CostGuard badges + audit exports.

6. **Stabilization (Week 6)**
   - Automated tests (Playwright), telemetry dashboards, accessibility audit.

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| API coverage incomplete (missing summary endpoints) | UI blocked waiting on backend | Parallel spec review; use mocked adapters until endpoints land |
| Spanish copy inconsistencies | User trust issues, rework | Centralized i18n strings, review with native speaker |
| Anthropic cost spikes from repeated agent runs | Budget surprise | Integrate CostGuard + caching; throttle identical prompts |
| Ontology tree scaling (100+ nodes) | Performance in browser | Virtualize tree rendering, lazy-load children |
| SQLite limitations before Postgres migration | Data freshness issues | Add caching layer + eventual Postgres cutover planned in Week 5 |

## 9. Success Metrics

- Time-to-insight: <2 min for consultant to produce draft deliverable.
- QA throughput: reduce unresolved contradictions by 40% week over week.
- Ontology approval SLA: 90% of proposals reviewed within 24h.
- Adoption: ≥5 active users across personas in pilot week.

---

This design doc will guide task planning (tickets per section) and serve as the reference for both Streamlit iterations and the forthcoming production web stack.


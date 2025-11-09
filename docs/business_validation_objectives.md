# Business Validation Objectives

This document captures the commercial intent behind the RAG 2.0 initiative so that technical requirements stay aligned with Grupo Conversa's digital-transformation offer.

## Purpose
- Validate the transformation offer by continuously surfacing cross-company insights from Bolivian Foods, Hotel Los Tajibos, and Comversa.
- Translate raw interviews (WhatsApp exports), documents (PDF/DOCX/CSV/XLSX/images/contracts), and system feeds into evidence for executive decisions.
- Keep AI operating costs within **$500–$1,000 USD/month** while maintaining compliance with Bolivian privacy statutes (Constitution Art. 21, Law 164, ATT guidelines).

## Core Questions to Answer Weekly
1. Which systems or processes create the largest pain points per company/business context?
2. How do WhatsApp interviews confirm or contradict current SAP/CRM assumptions?
3. Which Tier-1 and Tier-2 initiatives (coordination, KPI automation, ACIS training) show measurable ROI?
4. Where do contracts, internal reports, or spreadsheets reveal risks (delays, overruns, compliance gaps)?
5. Are we meeting ingestion ramp goals (10 docs/week → 10 docs/day) and keeping OCR/LLM usage under budget?

## Key Metrics
- Manual-reporting hours reduced, per organization
- Decision-cycle time deltas versus baseline
- Adoption of ACIS training cascade (10→30→90 participants)
- Data freshness (≤24 h KPI refresh) and ingestion throughput
- Compliance adherence (checkpoint approvals, Habeas Data readiness)

## Data Sources & Provenance
- WhatsApp conversation exports (primary interviews)
- PDFs/DOCX/contracts/images coming from departments (e.g., Bolivian Foods franchise folder)
- CSV/XLSX up to 24+ MB (financials, KPIs, inventories)
- Direct APIs or system dumps when available (SAP, Oracle OPERA, property management)
- All inputs tagged with `org_id`, `business_context`, `source_format`, and consent metadata to satisfy Bolivian regulations.

## Governance Expectations
- Review checkpoints after ingestion, OCR, consolidation, and pre-production responses.
- Snapshot outputs and approval decisions in `reports/checkpoints/{org_id}/{stage}/`.
- Maintain audit-ready logs so executive sponsors (Patricia, Samuel, Armando, etc.) can validate insights before they influence the offer.

## Phase Alignment
- **Phase 0 (Weeks 0-2):** Stand up context registry + ingestion namespace.
- **Phase 1 (Weeks 1-6):** Hit Tier-1 wins (coordination, KPI dashboards, training) using RAG insights.
- **Phase 2 (Weeks 7+):** Expand to additional systems, customer-journey intelligence, and Director AI deliverables once Phase 1 KPIs are met.

This document should be referenced whenever new requirements are drafted or prompts are updated to ensure the system continues to serve the business validation mission.

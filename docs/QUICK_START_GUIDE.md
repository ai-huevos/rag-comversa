# Phase 1 Quick Start Guide
## How to Use These Deliverables

**Last Updated**: 2025-10-23

---

## 📚 **What You Have**

6 documents totaling ~128KB of structured implementation guidance:

| Document | Purpose | Who Should Read | When to Use |
|----------|---------|-----------------|-------------|
| **PHASE1_EXECUTIVE_SUMMARY.md** | Overview & roadmap | Executives, all stakeholders | Start here - understand the big picture |
| **PHASE1_ONTOLOGY_SCHEMA.json** | Data model for AI | Technical architects, developers | When building Claude integrations |
| **PHASE1_KPI_DICTIONARY.json** | Performance metrics | Finance, Operations, all managers | Setting targets, tracking progress |
| **PHASE1_AGENT_PLAYBOOKS.json** | AI automation specs | Developers, process owners | Implementing specific agents |
| **PHASE1_SOP_PACK.md** | Human procedures | All staff, process owners | Day-to-day operations with AI |
| **PHASE1_AUTOMATION_BACKLOG.json** | Prioritized roadmap | PMO, steering committee | Planning sprints and resource allocation |

---

## 🚀 **Week 1 Action Plan**

### Day 1-2: Leadership Alignment
**Who**: General Managers, Operations Directors, Finance Directors
**Tasks**:
1. Read [PHASE1_EXECUTIVE_SUMMARY.md](PHASE1_EXECUTIVE_SUMMARY.md) (30 min)
2. Review Tier 1 automations in [PHASE1_AUTOMATION_BACKLOG.json](PHASE1_AUTOMATION_BACKLOG.json) (30 min)
3. Discuss and approve Phase 1 scope (2 hours meeting)
4. Assign executive sponsors per company

**Decisions Needed**:
- Budget allocation for Phase 1 ($X based on dev team mix)
- Internal vs external development resources
- Pilot automation selection (2-3 from Tier 1)
- Steering committee members

### Day 3-4: Technical Setup
**Who**: IT Managers, Technical Leads
**Tasks**:
1. API Access Audit:
   - Opera PMS API - request credentials
   - SAP/CMNET API - document endpoints
   - Simphony/Micros data export - confirm access
   - Satcom integration - validate data format
2. Infrastructure Setup:
   - WhatsApp Business API - register accounts (LTH, Comversa, BF)
   - Claude API - obtain keys (Anthropic)
   - MaintainX - confirm deployment status (LTH, BF)
   - ServiceDesk Plus API - enable if not active
3. Review [PHASE1_ONTOLOGY_SCHEMA.json](PHASE1_ONTOLOGY_SCHEMA.json) - understand data entities (1 hour)

**Deliverables**:
- API access inventory spreadsheet
- Infrastructure readiness checklist
- Technical risks identified

### Day 5: Operational Prep
**Who**: Department Managers, Process Owners
**Tasks**:
1. SOP Training Sessions:
   - Read [PHASE1_SOP_PACK.md](PHASE1_SOP_PACK.md) (1 hour)
   - Workshop: Intake Process (SOP-INTAKE-001) - 1 hour
   - Workshop: Approval Workflows (SOP-APPROVAL-001) - 1 hour
2. Data Cleanup Sprint Planning:
   - Asset register review (Maintenance)
   - Ingredient master data (Chef/Costos)
   - Contract template library (Legal)
3. KPI Baseline Measurement:
   - Review [PHASE1_KPI_DICTIONARY.json](PHASE1_KPI_DICTIONARY.json) (30 min)
   - Identify KPIs you own
   - Collect Month 0 baseline data

**Deliverables**:
- SOP training attendance roster
- Data cleanup task list with owners
- KPI baseline snapshot (what can be measured now)

---

## 🎯 **Using the Ontology Schema** (Developers)

### Purpose
[PHASE1_ONTOLOGY_SCHEMA.json](PHASE1_ONTOLOGY_SCHEMA.json) defines the data model Claude will use to understand your operations.

### Key Entities
- **InterviewResponse**: Manager inputs with responsibilities, tools, pain points
- **Process**: Workflows with inputs, outputs, systems, SLAs
- **System**: Software with integration points, owners, pain points
- **KPI**: Metrics with formula, baseline, target, data source
- **AutomationCandidate**: Automation opportunities with impact/effort scores
- **AgentPlaybook**: AI agent specifications
- **PainPoint**: Operational friction points

### How to Use
1. **Building RAG Store**: Use entity schema as collection structure in your vector DB
2. **Claude Prompts**: Reference entity types in prompts (e.g., "Find all Processes using SAP")
3. **API Design**: Structure your automation APIs to match output schemas
4. **Knowledge Graph**: Implement relationships to enable cross-entity reasoning

### Example Query
```
"Show me all PainPoints of type 'Data' that affect Finance processes and could be solved by AGENT-002 Reconciliation Bot"
```

---

## 📊 **Using the KPI Dictionary** (Managers)

### Purpose
[PHASE1_KPI_DICTIONARY.json](PHASE1_KPI_DICTIONARY.json) provides 24 performance metrics with baselines and 12-month targets.

### Your Role
1. **Identify Your KPIs**: Search by domain (Maintenance, Finance, Commercial, etc.) or owner role
2. **Baseline Current State**: Measure your Month 0 baseline (even if imperfect)
3. **Set Targets**: Review 3-month, 6-month, 12-month targets - adjust if needed
4. **Track Progress**: Update actual values monthly
5. **Link to Automations**: See which automations improve your KPIs

### Example: Gerente de Ingeniería (LTH)
**Your KPIs**:
- MNT-001: PM Completion Rate (target: 60% → 75% → 85%)
- MNT-002: MTTR (target: < 24h critical → < 12h → < 8h)
- MNT-003: Preventive vs Reactive Ratio (target: 40% → 55% → 70%)

**Automation Support**:
- AUTO-T1-003: PM Scheduler - directly improves MNT-001 and MNT-003

**Action**: Measure current PM completion % and MTTR this month (baseline)

---

## 🤖 **Using Agent Playbooks** (Developers & Process Owners)

### Purpose
[PHASE1_AGENT_PLAYBOOKS.json](PHASE1_AGENT_PLAYBOOKS.json) provides production-ready specifications for 5 Claude agents.

### Implementation Steps (per agent)
1. **Read Full Playbook**: Understand purpose, triggers, and guardrails
2. **Review Prompt Template**: This is your Claude system prompt
3. **Implement Output Schema**: Structure your API responses to match
4. **Configure Guardrails**: Implement allowed/forbidden actions and escalation logic
5. **Set Up Audit Logging**: Log all required audit fields
6. **Link to SOPs**: Ensure human procedures align (e.g., AGENT-001 → SOP-INTAKE-001)
7. **Test with Sample Interaction**: Use provided examples to validate

### Example: AGENT-001 Intake Router
**Trigger**: WhatsApp message to intake number
**Action**: Classify, route, acknowledge
**Output**: Ticket in MaintainX/ServiceDesk, acknowledgment sent
**Guardrails**: Cannot resolve without human approval, escalates if low confidence
**SOP**: SOP-INTAKE-001 defines human responsibilities
**Test**: Send sample maintenance request, verify routing to MaintainX

---

## 📋 **Using SOP Pack** (All Staff)

### Purpose
[PHASE1_SOP_PACK.md](PHASE1_SOP_PACK.md) defines human procedures that work with AI agents.

### 4 Critical SOPs

#### **SOP-INTAKE-001: One-Door Intake**
**Who**: All staff (requesters), supervisors (assigners)
**What**: Submit ALL requests via WhatsApp Business, intake@email, or web form
**Why**: Eliminates lost requests, enables SLA tracking
**Action**: Bookmark intake channels, stop using personal WhatsApp/verbal requests

#### **SOP-APPROVAL-001: Approval Workflows**
**Who**: All managers (approvers)
**What**: Approve/reject via system within SLA (PO: 4h-5 days, Payments: 24-48h, Contracts: 3-10 days)
**Why**: Eliminates bottlenecks, enables automation
**Action**: Review authority matrix, commit to SLA compliance

#### **SOP-EVIDENCE-CLOSURE-001: Evidence-Based Closure**
**Who**: Process owners (maintenance, IT, quality)
**What**: Close tickets only with photos, checklists, test results, requester signoff
**Why**: Prevents rework, provides audit trail
**Action**: Upload evidence before marking "Pending Closure"

#### **SOP-DATA-CHANGE-001: Data Change Control**
**Who**: Data owners (prices, recipes, KPIs, configs)
**What**: All critical data changes require approval and audit trail
**Why**: Prevents errors, maintains data integrity
**Action**: Submit change request form, document before/after values

### Training Plan
- **Week 1**: SOP-INTAKE-001 training (all staff, 1 hour)
- **Week 2**: SOP-APPROVAL-001 training (managers, 1 hour)
- **Week 3**: SOP-EVIDENCE-CLOSURE-001 training (ops teams, 1 hour)
- **Week 4**: SOP-DATA-CHANGE-001 training (data owners, 1 hour)

---

## 🗓️ **Using Automation Backlog** (PMO & Steering Committee)

### Purpose
[PHASE1_AUTOMATION_BACKLOG.json](PHASE1_AUTOMATION_BACKLOG.json) prioritizes 15 automations by ROI across 12 months.

### How to Plan Sprints

#### **Month 1-3: Tier 1 Quick Wins** (6 automations, $236K value)
**Sprint Planning**:
1. Review Tier 1 section (page 1-10)
2. Select 2-3 automations for Phase 1a pilot
3. Assign resources: 2 developers, 1 BA, SMEs
4. Set sprint goals: Classification accuracy, SLA tracking, time savings

**Recommended Pilot Order**:
1. AUTO-T1-001: Intake Router (universal benefit, foundational)
2. AUTO-T1-002: Reconciliation Bot (high pain point, measurable savings)
3. AUTO-T1-003: PM Scheduler (strategic, visible improvement)

#### **Month 4-6: Tier 2 High Value** (6 automations, $182K value)
After Tier 1 success, expand to domain-specific automations.

#### **Month 7-12: Tier 3 Strategic** (3 automations, $280K value)
Transformational projects requiring significant investment.

### Sprint Template
```markdown
## Sprint: AUTO-T1-001 Intake Router

**Duration**: 3 weeks
**Team**: 2 devs (Backend/Integration), 1 BA, SMEs (Ingeniería, IT, Legal)
**Goal**: Route 80% of requests via automated intake by end of sprint

**Week 1**: API setup (WhatsApp, MaintainX, ServiceDesk), classification model training
**Week 2**: Integration development, acknowledgment flows, SLA tracking
**Week 3**: Testing, training sessions, pilot launch (1 department)

**Success Criteria**:
- Classification accuracy > 80% (target: 85%)
- Routing time < 5 minutes
- Acknowledgment sent 100%
- User feedback > 70% satisfied
```

---

## 🔄 **Integration Workflow**

### How the Pieces Work Together

```
Manager Interview (CSV)
    ↓
Ontology Schema (data model)
    ↓
Knowledge Graph (Claude's understanding)
    ↓
Agent Playbook (automation spec) ←→ SOP (human procedure)
    ↓
Automation Implementation (code)
    ↓
KPI Tracking (results measurement)
    ↓
Backlog Refinement (learn and improve)
```

### Example Flow: Maintenance Request
1. **Staff**: Submits request via WhatsApp (per SOP-INTAKE-001)
2. **AGENT-001**: Classifies as "Maintenance - High urgency" (per Playbook)
3. **System**: Creates MaintainX ticket, assigns to Jefe de Ingeniería, sets 24h SLA
4. **Human**: Technician completes work, uploads photos (per SOP-EVIDENCE-CLOSURE-001)
5. **AGENT-004**: Validates evidence completeness, routes for requester approval
6. **Human**: Requester approves, ticket closed
7. **KPI**: MTTR tracked, PM completion rate updated (per KPI Dictionary)
8. **Report**: Monthly metrics show improvement, automation ROI validated

---

## ❓ **FAQ**

### Q: Which document should I read first?
**A**: [PHASE1_EXECUTIVE_SUMMARY.md](PHASE1_EXECUTIVE_SUMMARY.md) - 15 min read, covers everything at executive level.

### Q: How technical is the Ontology Schema?
**A**: Very. It's JSON for developers building Claude integrations. Non-technical users can skip it.

### Q: Can I modify the KPI targets?
**A**: Yes! Targets are recommendations. Adjust based on your baseline and business context.

### Q: Do I have to implement all 15 automations?
**A**: No. Start with Tier 1 (6 automations). Tier 2-3 are options based on Phase 1 success.

### Q: What if my team doesn't use MaintainX yet?
**A**: Deploy MaintainX first (or choose alternative CMMS) before implementing maintenance automations.

### Q: Are the SOPs mandatory?
**A**: Yes, for successful AI integration. Agents automate classification/routing, humans provide judgment and approvals.

### Q: How much does Phase 1 cost?
**A**: Depends on dev team mix (internal vs external). Estimated 165 effort-days for Tier 1. Add infrastructure costs (WhatsApp Business API, Claude API, MaintainX licenses).

### Q: When will we see ROI?
**A**: Quick wins deliver value in Month 2-3 (time savings measurable). Full $236K Tier 1 value realized by Month 6.

---

## 📞 **Getting Help**

### Technical Questions
- **API Access**: IT Managers (Gerente de IT - LTH, Subgerente TI - Comversa, Jefe Nacional Sistemas - BF)
- **Development**: Technical leads, external development partner

### Process Questions
- **Maintenance**: Gerente de Ingeniería (LTH), Jefe Nacional de Mantenimiento (BF)
- **Finance**: Gerente de Control de Gestión (LTH), Gerente de Finanzas (Comversa/BF)
- **Commercial**: Directora Comercial (Comversa), Directora Marketing y Ventas (LTH)
- **Legal**: Directora Legal (Comversa)
- **Logistics**: Subgerente de Logística (BF)

### Strategic Questions
- **Phase 1 Scope**: Steering committee
- **Budget/Resources**: General Managers
- **Change Management**: Operations Directors

---

## ✅ **Success Checklist (Month 1)**

- [ ] Executive team reviewed summary and approved Phase 1 scope
- [ ] Steering committee formed with monthly meeting cadence
- [ ] Budget allocated for Phase 1 (dev resources, infrastructure)
- [ ] API access audit completed
- [ ] WhatsApp Business accounts registered (3 companies)
- [ ] MaintainX deployment confirmed (LTH, BF)
- [ ] SOP training sessions scheduled (4 SOPs × 3 companies = 12 sessions)
- [ ] KPI baseline measurement initiated (24 KPIs)
- [ ] Pilot automations selected (2-3 from Tier 1)
- [ ] Sprint 1 kickoff scheduled

**Once complete**: You're ready to start building! 🚀

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-23
**Next Update**: Post-Phase 1 completion (Month 3)

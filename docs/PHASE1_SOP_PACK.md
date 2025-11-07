# Phase 1 SOP Pack
## Standard Operating Procedures for AI-Ready Operations

**Version**: 1.0.0
**Date**: 2025-10-23
**Scope**: Los Tajibos, Comversa, Bolivian Foods
**Purpose**: Human procedures that pair with AI agent automation

---

## SOP-INTAKE-001: One-Door Intake Process

### Purpose
Establish single entry point for all operational requests to eliminate scattered communication, duplicate entries, and lost requests.

### Scope
All requests for: Maintenance, IT Support, Finance, Legal, Logistics, Commercial support, HR matters

### Applicable Companies
Los Tajibos, Comversa, Bolivian Foods

### Process Flow

#### 1. Request Submission
**Requesters must use ONLY approved channels**:
- **WhatsApp Business**: Company intake number (to be established)
- **Email**: intake@[company].com
- **Web Form**: Intranet portal (Phase 2)
- **Direct System Entry**: MaintainX (maintenance), ServiceDesk Plus (IT)

**Forbidden channels** (will NOT be processed):
- Personal WhatsApp
- Personal emails
- Verbal requests (unless emergency/safety)
- Sticky notes, paper forms

**Required information**:
- Your name and department
- Nature of request (brief description)
- Urgency level (see classification below)
- Location/Asset ID (if applicable)
- Photos/documents (if relevant)
- Preferred response channel

#### 2. Intake Agent Processing
**Automated** (AGENT-001 Intake Router):
- Receives request within 5 minutes
- Classifies request type and urgency
- Routes to appropriate system and owner
- Assigns ticket ID
- Sets SLA deadline
- Sends acknowledgment to requester

**Acknowledgment includes**:
- Ticket ID (e.g., MNT-2510-1045)
- Request type and urgency
- Assigned owner (role, not person)
- SLA deadline (date/time)
- How to track status

#### 3. Urgency Classification

| Level | Definition | Response SLA | Examples |
|-------|-----------|--------------|----------|
| **Critical** | Safety risk, revenue loss, guest impact, system down | 8 hours | Guest room HVAC failure, POS system down, safety hazard, VIP complaint |
| **High** | Operational impact, deadline pressure | 24 hours | Equipment malfunction (non-guest), urgent contract review, delayed shipment |
| **Standard** | Normal operations, no immediate impact | 48 hours | Routine maintenance, data requests, standard approvals |
| **Low** | Planning, non-urgent improvements | 5 business days | Process improvement ideas, training requests, reporting enhancements |

#### 4. Request Tracking
**For Requesters**:
- Check status anytime via ticket ID
- Receive updates on status changes
- Get notified 24h before SLA deadline if pending
- Approve closure or request follow-up

**For Owners**:
- View assigned queue in system
- Update status and add notes
- Request SLA extension with justification (requires supervisor approval)
- Close with evidence per SOP-EVIDENCE-CLOSURE-001

#### 5. Escalation Process
**Auto-escalation triggers**:
- SLA approaching (80% elapsed) with no progress update
- Requester marks as "not resolved" on closure attempt
- Multiple related requests from same source
- Critical request not acknowledged within 1 hour

**Escalation path**:
1. Assigned owner → Department supervisor
2. Supervisor → Area manager
3. Manager → Operations director / General manager

#### 6. Quality Metrics
**Tracked KPIs**:
- % requests via approved channels (target: 95%)
- Classification accuracy (target: 90%)
- SLA compliance rate (target: 85%)
- Mis-routing rate (target: < 5%)
- Requester satisfaction (quarterly survey)

### Roles & Responsibilities

| Role | Responsibility |
|------|----------------|
| **All Staff** | Submit requests ONLY via approved channels; provide complete information |
| **Intake Agent (AI)** | Classify, route, acknowledge, track SLA |
| **Department Supervisors** | Assign to team members, monitor queue, approve SLA extensions |
| **Process Owners** | Resolve requests within SLA, update status, close with evidence |
| **IT Team** | Maintain intake systems, troubleshoot agent issues |

### Training Requirements
- New hire orientation: Intake process overview (15 min)
- Monthly refresher: Correct channel usage
- Quarterly review: Metrics and improvements

---

## SOP-APPROVAL-001: Approval Workflow & SLAs

### Purpose
Standardize approval processes to eliminate bottlenecks, clarify authority levels, and enable automation.

### Scope
Approvals for: Purchase orders, Payment requests, Contracts, Budget variances, Policy exceptions

### Approval Authority Matrix

#### Purchase Orders
| Amount (Bs) | Approver | SLA |
|-------------|----------|-----|
| < 5,000 | Department Supervisor | 4 hours |
| 5,000 - 20,000 | Department Manager | 24 hours |
| 20,000 - 100,000 | Area Director + Finance | 48 hours |
| > 100,000 | General Manager + Finance Director | 5 business days |

#### Payment Requests
| Type | Approver | SLA |
|------|----------|-----|
| Vendor invoice (with PO) | Accounts Payable | 24 hours |
| Vendor invoice (no PO) | Department Manager + AP | 48 hours |
| Reimbursement < Bs 2,000 | Department Supervisor | 24 hours |
| Reimbursement > Bs 2,000 | Department Manager | 48 hours |

#### Contracts
| Type | Approver | SLA |
|------|----------|-----|
| Template contract < Bs 50,000 | Legal + Department Manager | 3 business days |
| Template contract > Bs 50,000 | Legal + Area Director + Finance | 5 business days |
| Custom contract | Legal + Department Manager + Finance + GM | 10 business days |
| Contract amendments | Original approvers | 5 business days |

#### Budget Variances
| Variance % | Approver | SLA |
|------------|----------|-----|
| < 10% | Department Manager | 24 hours |
| 10-20% | Area Director | 48 hours |
| > 20% | Finance Director + GM | 5 business days |

### Process Flow

#### 1. Request Submission
**Requester**:
- Completes approval request form (digital)
- Attaches all required documentation
- Specifies urgency and business justification
- Submits via workflow system

**Required documentation**:
- **PO**: Supplier quote, budget allocation code
- **Payment**: Invoice, PO (if applicable), delivery confirmation
- **Contract**: Draft document, business case, risk assessment
- **Budget**: Variance explanation, mitigation plan, updated forecast

#### 2. Automated Routing
**System** (AI-assisted):
- Validates completeness of documentation
- Determines approval path per matrix
- Routes to first approver
- Sets SLA timer
- Sends notification (email + system alert)

#### 3. Approval Actions
**Approver options**:
- **Approve**: Proceeds to next approver or final
- **Reject**: Returns to requester with reason
- **Request Changes**: Sends back with specific change requests
- **Delegate**: Transfers to alternate approver (same level) with notification

**Approval must include**:
- Digital signature or system confirmation
- Comments (if reject/request changes)
- Timestamp

#### 4. SLA Management
**Approaching SLA** (80% elapsed):
- Auto-reminder to pending approver
- Notification to requester
- Option to escalate to supervisor

**SLA Exceeded**:
- Auto-escalates to approver's supervisor
- Logs SLA breach
- Requester notified of escalation

**SLA Extension Requests**:
- Approver can request extension with justification
- Requires supervisor approval
- Limited to 1 extension per approval step
- Requester notified of delay and reason

#### 5. Final Approval Actions
**On approval**:
- Requester notified
- Finance/Purchasing triggered for execution
- Approval archived for audit
- Approval metrics updated

**On rejection**:
- Requester notified with detailed reason
- Option to resubmit with corrections
- Rejection reason logged for analysis

### Parallel vs Sequential Approvals

**Parallel** (all approvers notified simultaneously):
- Multi-signature contracts (Legal + Finance + Department)
- Budget reviews requiring independent assessment
- **Closes when**: ALL approvers confirm

**Sequential** (one approver at a time):
- Hierarchical approvals (Supervisor → Manager → Director)
- Dependent approvals (Technical review → Financial review)
- **Closes when**: Final approver in chain confirms

### Emergency Override
**Emergency approvals** (Critical urgency):
- **Trigger**: Safety, revenue protection, legal deadline
- **Process**: Verbal approval + documentation within 24h
- **Requires**: Post-approval ratification by next higher authority
- **Audit**: All emergency overrides reviewed monthly

### Quality Metrics
**Tracked KPIs**:
- Average approval cycle time by type
- SLA compliance rate (target: 90%)
- Rejection rate (investigate if > 15%)
- Resubmission rate (target: < 10%)
- Emergency override frequency (target: < 2% of approvals)

### Audit Trail Requirements
All approvals must log:
- Requester identity and timestamp
- Approval path and sequence
- Each approver's action and timestamp
- Documents attached (versioned)
- SLA compliance status
- Final outcome and execution confirmation

---

## SOP-EVIDENCE-CLOSURE-001: Evidence-Based Closure

### Purpose
Ensure work completion is validated with objective evidence before closure to prevent rework, disputes, and quality issues.

### Scope
Closure of: Maintenance work orders, IT tickets, Project deliverables, Quality inspections, Training completions

### Evidence Requirements by Request Type

#### Maintenance Work Orders
**Minimum evidence**:
1. **Before photos**: Showing issue or equipment state
2. **During photos**: Work in progress (critical steps)
3. **After photos**: Completed work
4. **Checklist**: All planned tasks checked off
5. **Parts used**: List with SAP/CMNET reference
6. **Test results**: Equipment tested and operational
7. **Requester signoff**: Confirmation work is satisfactory

**Additional for preventive maintenance**:
- Manufacturer checklist completed
- Measurements recorded (pressure, temperature, voltage, etc.)
- Next PM due date updated

#### IT Support Tickets
**Minimum evidence**:
1. **Issue description**: Screenshots or error messages
2. **Resolution steps**: Actions taken
3. **Verification**: Screenshot or log showing issue resolved
4. **User confirmation**: Requester confirms system working
5. **Knowledge base**: Link to KB article if applicable

**Additional for infrastructure**:
- Configuration changes documented
- Backup/rollback plan confirmed
- Monitoring alerts cleared

#### Contracts (Legal/Commercial)
**Minimum evidence**:
1. **Signed contract**: All party signatures and dates
2. **Approval trail**: All internal approvals logged
3. **Delivery confirmation**: Contract sent to parties
4. **Archive confirmation**: Filed in document repository
5. **Key dates**: Extracted and added to calendar (renewals, milestones)

#### Quality Inspections
**Minimum evidence**:
1. **Inspection checklist**: All items completed
2. **Non-conformities**: Photos and descriptions of any issues
3. **Corrective actions**: Plan for issues found
4. **Signoff**: Inspector and area manager
5. **Follow-up**: Date scheduled for re-inspection if needed

### Closure Process Flow

#### 1. Work Completion
**Owner**:
- Completes all planned work
- Gathers required evidence
- Updates ticket/work order status to "Pending Closure"
- Uploads evidence to system
- Notifies requester for validation

#### 2. Evidence Validation
**System** (AI-assisted):
- Checks mandatory fields completed
- Verifies evidence attachments present
- Flags missing items
- Routes to requester for approval

**If evidence incomplete**:
- Ticket returned to owner with specific gaps listed
- Cannot proceed to closure
- SLA timer continues

#### 3. Requester Validation
**Requester**:
- Reviews evidence
- Physically inspects if needed
- Chooses action:
  - **Approve**: Work satisfactory, close ticket
  - **Request Follow-up**: Additional work needed
  - **Escalate**: Quality concern, supervisor review

**SLA for requester validation**: 24 hours (else auto-escalate to supervisor)

#### 4. Final Closure
**On approval**:
- Ticket status → "Closed"
- Closure timestamp recorded
- Evidence archived for audit
- Metrics updated (resolution time, quality score)
- Requester receives closure summary

**If follow-up requested**:
- Ticket status → "Reopened"
- Additional work planned
- New SLA set
- Original closure attempt logged

### Evidence Storage & Retention

**Storage requirements**:
- All evidence in centralized system (MaintainX, ServiceDesk, SharePoint)
- No evidence on personal devices or local drives
- Photos: Max 5MB each, JPEG format
- Documents: PDF format
- Naming convention: [TicketID]_[Type]_[Sequence]

**Retention periods**:
- Maintenance: 5 years (equipment lifecycle)
- IT: 2 years (unless security incident: 7 years)
- Contracts: Per contract term + 3 years
- Quality inspections: 3 years (unless regulatory: per regulation)

### Quality Metrics
**Tracked KPIs**:
- Evidence completeness rate (target: 95%)
- Requester approval rate (target: > 90%)
- Reopen rate (target: < 5%)
- Evidence upload time (target: within 2 hours of work completion)

### Roles & Responsibilities

| Role | Responsibility |
|------|----------------|
| **Work Owner** | Complete work, gather evidence, upload to system, notify requester |
| **Requester** | Validate evidence within 24h, approve or request follow-up |
| **Supervisor** | Review escalated closures, approve overrides if justified |
| **Quality Team** | Spot-check evidence quality, provide training if gaps found |

---

## SOP-DATA-CHANGE-001: Data Change Control

### Purpose
Prevent errors in master data and critical records through controlled change processes with approvals and audit trails.

### Scope
Changes to: Prices, Recipes, KPI definitions, Chart of accounts, User permissions, System configurations, Contracts

### Classification of Data Changes

#### Tier 1: Low-Risk Changes
**Examples**: Descriptive text, contact information, non-financial data
**Approval**: Data owner
**Documentation**: Change log entry
**SLA**: 24 hours

#### Tier 2: Medium-Risk Changes
**Examples**: Non-critical prices, recipe adjustments, report formats
**Approval**: Data owner + Department manager
**Documentation**: Change request form + before/after values
**SLA**: 48 hours

#### Tier 3: High-Risk Changes
**Examples**: Critical prices (menu items, materials), KPI formulas, accounting codes, system integrations
**Approval**: Data owner + Department manager + Finance/IT director
**Documentation**: Change request + impact analysis + testing plan
**SLA**: 5 business days

### Process Flow

#### 1. Change Request Submission
**Requester completes form**:
- What data/record is changing
- Current value vs proposed value
- Business justification
- Impact assessment (systems, reports, processes affected)
- Effective date
- Rollback plan (Tier 3 only)

#### 2. Impact Analysis
**Data Owner**:
- Reviews request
- Identifies all affected systems and reports
- Assesses risk tier
- Determines approval path
- Routes to approvers

**For Tier 3 changes**:
- **IT**: System impact assessment
- **Finance**: Financial statement impact
- **Audit**: Compliance implications

#### 3. Approval & Testing
**Approvers**:
- Review impact analysis
- Approve, reject, or request more information
- All approvers must confirm for Tier 3

**Testing (Tier 3 only)**:
- Changes tested in non-production environment
- Results documented
- Approvers confirm test success

#### 4. Implementation
**Data Owner**:
- Schedules change for approved effective date
- Coordinates with IT if system changes needed
- Implements change
- Validates change in production
- Notifies affected users

**Version Control**:
- Before value archived
- After value timestamped
- Change log updated
- Audit trail complete

#### 5. Post-Implementation Validation
**Within 48 hours**:
- Data owner confirms change working as expected
- Affected reports validated
- Users confirm no unexpected impacts
- Rollback triggered if issues found

### Critical Data Change Examples

#### Price Changes (SAP/CMNET)
**Requester**: Purchasing/Costos
**Approvers**: Department manager + Finance
**Impact analysis**: Recipe costs, menu pricing, budget variance
**Effective date**: Typically 1st of month
**Notification**: Chef, Finance, Costos

#### Recipe Modifications
**Requester**: Chef
**Approvers**: Chef + Costos
**Impact analysis**: Food cost %, menu item pricing
**Version control**: Recipe versions tracked
**Notification**: Kitchen, Service, Costos

#### KPI Definition Changes
**Requester**: Control de Gestión
**Approvers**: Department manager + Finance Director
**Impact analysis**: Historical trends, targets, dashboard reports
**Retroactive application**: Requires additional approval
**Notification**: All users of KPI reports

#### User Permission Changes
**Requester**: Department manager
**Approvers**: IT + Security
**Impact analysis**: Access to sensitive data/systems
**Audit**: All permission changes reviewed quarterly
**Notification**: User, IT, Audit

### Emergency Changes
**Trigger**: Production issue, data error causing operational impact
**Process**:
1. Verbal approval from department manager
2. Implement change
3. Document change within 4 hours
4. Post-approval by all required approvers within 24 hours
5. Root cause analysis if systemic issue

**Audit**: All emergency changes reviewed monthly

### Data Sources of Truth

| Data Domain | System of Record | Owner | Update Frequency |
|-------------|------------------|-------|------------------|
| **Guest reservations** | Opera PMS | Recepción | Real-time |
| **Sales transactions** | Simphony/Micros | Operations | Real-time |
| **Financial GL** | SAP | Contabilidad | Daily close |
| **Inventory** | SAP/CMNET | Logistics | Daily |
| **Invoicing** | Satcom | Facturación | Daily |
| **Asset register** | MaintainX | Ingeniería | Monthly |
| **Contracts** | Legal repository | Legal | Per execution |
| **Pricing** | SAP/CMNET | Purchasing | Weekly/Event-driven |
| **Recipes** | Recipe DB | Chef | Monthly |
| **KPIs** | Control de Gestión | Finance/Ops | Monthly |

**Cross-system reconciliation**:
- Opera ↔ Satcom: Daily (revenue)
- SAP ↔ CMNET: Weekly (inventory)
- Budget ↔ Actuals: Monthly

### Quality Metrics
**Tracked KPIs**:
- Change approval cycle time
- Data error rate (errors per 1000 records)
- Emergency change frequency (target: < 5% of changes)
- Rollback rate (target: < 2%)
- User-reported data issues (trend toward zero)

### Roles & Responsibilities

| Role | Responsibility |
|------|----------------|
| **Data Owner** | Maintain data quality, review change requests, coordinate implementation |
| **Requester** | Complete change request form, provide business justification |
| **Approvers** | Assess impact, approve/reject within SLA |
| **IT Team** | Implement system changes, maintain audit logs |
| **Audit** | Review change compliance quarterly, investigate errors |

---

## SOP Integration with AI Agents

### How SOPs & Agents Work Together

| SOP | Paired Agent | Integration |
|-----|--------------|-------------|
| **SOP-INTAKE-001** | AGENT-001 Intake Router | Agent performs classification and routing; humans follow escalation paths |
| **SOP-APPROVAL-001** | All agents (approval routing) | Agents route for approval per matrix; humans approve/reject; agent tracks SLA |
| **SOP-EVIDENCE-CLOSURE-001** | AGENT-004 PM Scheduler | Agent validates evidence completeness; humans provide evidence and signoff |
| **SOP-DATA-CHANGE-001** | AGENT-003 Recipe Costing | Agent uses approved prices (source of truth); humans approve price changes |

### Human Judgment Zones
**Agents automate**: Classification, routing, validation checks, notifications, reporting
**Humans decide**: Approvals, policy exceptions, quality judgments, escalations, strategy

### SOP Maintenance
- **Quarterly review**: Process owners validate SOPs still accurate
- **Annual update**: Incorporate lessons learned and process improvements
- **Change control**: SOP modifications require manager approval
- **Training**: All SOP changes communicated within 2 weeks

---

## Implementation Roadmap

### Month 1: Foundation
- Publish SOPs to all staff
- Training sessions by department
- Activate intake channels (WhatsApp Business, email)
- Deploy AGENT-001 Intake Router
- Measure baseline: request sources, approval times, closure compliance

### Month 2: Optimization
- Analyze Month 1 metrics
- Refine agent classification accuracy
- Adjust approval thresholds based on data
- Implement evidence templates in MaintainX
- Begin data source of truth documentation

### Month 3: Expansion
- Deploy remaining agents (AGENT-002 through AGENT-005)
- Full automation of approval routing
- Evidence validation checks active
- Data change control integrated with SAP/CMNET workflows
- First quarterly SOP review

**Success Criteria**:
- 90% requests via approved channels by Month 3
- SLA compliance > 85% by Month 3
- Evidence completeness > 90% by Month 3
- Data change control tracking 100% of Tier 3 changes

---

**Document Control**
**Owner**: Operations Directors (LTH, Comversa, BF)
**Approvers**: General Managers
**Review Frequency**: Quarterly
**Next Review**: 2025-01-23
**Distribution**: All managers and supervisors

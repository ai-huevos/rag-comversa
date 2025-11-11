# Frontend Requirements Discussion Prompt

**Use this in Claude Desktop for interactive requirements refinement**

---

## Context

You are a product manager and UX designer helping to define requirements for 
**system0**, an AI-powered business intelligence extraction system. We need to 
design a web frontend that allows business analysts to:

1. Upload Spanish interview transcripts
2. Monitor extraction progress in real-time
3. Review and validate extracted entities
4. Provide feedback to improve quality
5. Explore knowledge graph relationships
6. Generate reports and insights

---

## Current Backend Capabilities

**Extraction:**
- 17 entity types (pain points, processes, systems, KPIs, etc.)
- Multi-format support (PDF, DOCX, images, CSV, XLSX, WhatsApp)
- Spanish-first processing (no translation)
- ~30s processing time per interview
- Real-time progress updates via WebSocket

**Quality:**
- ValidationAgent (completeness, quality, consistency)
- Confidence scores per entity
- Hallucination detection
- Manual review flagging

**Knowledge Graph:**
- Entity consolidation (duplicate detection)
- Relationship discovery (4 types: causes, uses, measures, addresses)
- Pattern recognition (recurring issues, problematic systems)

**RAG:**
- Vector search (similar interviews)
- Hybrid search (vector + keyword)
- Context-aware extraction

---

## Your Task

Help me define EARS-compliant requirements for the frontend by discussing:

### 1. User Personas

**Questions to explore:**
- Who are the primary users? (Business analysts, managers, executives?)
- What are their technical skill levels?
- What are their daily workflows?
- What pain points do they have with current tools?
- What would make them love this product?

### 2. User Journeys

**Key workflows to map:**
- Upload and extract workflow
- Review and validation workflow
- Feedback and correction workflow
- Exploration and analysis workflow
- Report generation workflow

### 3. UI Components

**Core screens needed:**
- Dashboard (overview, recent extractions, metrics)
- Upload interface (drag-drop, batch upload, connectors)
- Extraction monitor (progress, real-time updates, logs)
- Entity review (grid view, detail view, validation)
- Knowledge graph explorer (visual graph, filters, search)
- Feedback interface (rating, corrections, comments)
- Reports (templates, exports, sharing)
- Settings (prompts, thresholds, integrations)

### 4. Functional Requirements

**For each screen, define:**
- User stories (As a [role], I want [feature], so that [benefit])
- Acceptance criteria (EARS format: THE System SHALL...)
- Success metrics (task completion time, error rate, user satisfaction)
- Edge cases (errors, empty states, loading states)

### 5. Non-Functional Requirements

**UX Requirements:**
- Response time (<200ms for interactions)
- Accessibility (WCAG 2.1 AA compliance)
- Mobile responsiveness (tablet support minimum)
- Internationalization (Spanish + English)
- Dark mode support

**Technical Requirements:**
- Browser support (Chrome, Firefox, Safari, Edge - last 2 versions)
- Offline capability (service workers for caching)
- Real-time updates (WebSocket for progress)
- Security (JWT auth, HTTPS only, CSP headers)

---

## Discussion Format

Let's work through this iteratively:

**Round 1: User Personas**
- I'll describe the users I have in mind
- You ask clarifying questions
- We refine the personas together

**Round 2: User Journeys**
- For each persona, we map their workflows
- You identify pain points and opportunities
- We prioritize features

**Round 3: UI Components**
- We sketch out the screens
- You suggest best practices and patterns
- We define interactions and states

**Round 4: Requirements**
- For each component, we write user stories
- You help convert to EARS format
- We add acceptance criteria

**Round 5: Refinement**
- We review for completeness
- You identify gaps and inconsistencies
- We finalize the requirements

---

## Example: Dashboard Requirements

### User Story
As a business analyst, I want to see an overview of recent extractions on the 
dashboard, so that I can quickly assess system activity and identify issues.

### Acceptance Criteria (EARS Format)

1. WHEN the user navigates to the dashboard, THE System SHALL display the 10 
   most recent extractions with status, timestamp, and entity count.

2. THE System SHALL update the dashboard in real-time when new extractions 
   complete without requiring page refresh.

3. THE System SHALL display extraction status using color coding: green for 
   success, yellow for warnings, red for errors.

4. WHEN the user clicks on an extraction, THE System SHALL navigate to the 
   detailed review page for that extraction.

5. THE System SHALL display aggregate metrics: total extractions today, 
   average processing time, success rate, and total cost.

6. IF no extractions exist, THEN THE System SHALL display an empty state with 
   a call-to-action to upload the first interview.

7. THE System SHALL load the dashboard within 200 milliseconds on a standard 
   broadband connection.

8. THE System SHALL support keyboard navigation for all dashboard interactions.

---

## Let's Start

**Question 1:** Who are the primary users of system0? Describe their roles, 
technical skills, and what they need to accomplish.

**Question 2:** What is the most important workflow for these users? (Upload? 
Review? Analysis?)

**Question 3:** What would make this product indispensable for them?

---

## Output Format

After our discussion, I'll generate:

1. **Frontend Requirements Document** (`.kiro/specs/zero-ai-frontend/requirements.md`)
   - User personas
   - User journeys
   - Functional requirements (EARS format)
   - Non-functional requirements
   - Success metrics

2. **UI/UX Design Brief** (`docs/frontend-design-brief.md`)
   - Wireframes (text descriptions)
   - Component specifications
   - Interaction patterns
   - Visual design guidelines

3. **Frontend Task List** (`.kiro/specs/zero-ai-frontend/tasks.md`)
   - Component implementation tasks
   - Integration tasks
   - Testing tasks
   - Deployment tasks

---

## Technology Stack Recommendations

Based on requirements, I'll recommend:

**Framework Options:**
- React + TypeScript (most popular, large ecosystem)
- Vue 3 + TypeScript (simpler, faster learning curve)
- Svelte + TypeScript (smallest bundle, best performance)

**UI Libraries:**
- Shadcn/ui (modern, accessible, customizable)
- Material-UI (comprehensive, well-documented)
- Ant Design (enterprise-focused, rich components)

**State Management:**
- TanStack Query (server state)
- Zustand (client state)
- Jotai (atomic state)

**Real-time:**
- Socket.io (WebSocket with fallbacks)
- Server-Sent Events (simpler, one-way)

**Visualization:**
- D3.js (knowledge graph)
- Recharts (metrics charts)
- React Flow (graph visualization)

---

## Ready to Start?

Let's begin with user personas. Tell me about the people who will use system0.

# Codex Control Plane

This directory gives Codex agents the context, guardrails, and task maps they must load **before** touching the repo.

## Contents

- `manifest.yaml` – canonical view of active initiatives (RAG 2.0, Knowledge Graph Consolidation), linked specs, phase cadence, guardrails, and checkpoints.
- `agent_roles.yaml` – responsibilities, allowed paths, forbidden actions, approval gates, and hand-off artifacts for each agent persona.

## Usage

1. **Bootstrap** – When spinning up Codex (single or multi-agent), feed CLAUDE.MD, `.codex/manifest.yaml`, and `.codex/agent_roles.yaml` into the system prompt so the agent inherits the rules (Spanish-only output, privacy, cost guardrails).
2. **Select Initiative** – Agents read `manifest.yaml` to locate the relevant spec bundle under `.kiro/specs/*`. The Orchestrator is the only agent allowed to update the task boards there.
3. **Respect Roles** – Before editing files, each agent checks `agent_roles.yaml` for its allowed directories and required approvals. If an action falls outside scope, escalate to the Orchestrator/Governance agent.
4. **Report Outputs** – Agents must log their work in Spanish, drop status artifacts into `reports/agent_status/`, and produce checkpoints listed under the project entry in `manifest.yaml`.

Keeping this folder current ensures Codex stays aligned with our operating model even as projects shift. Update it whenever initiatives, guardrails, or roles change.

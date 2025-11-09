# Codex Bootstrap Instructions

Always load these files into Codex/Claude sessions (CLI or IDE) **in this order** before writing code:

1. `CLAUDE.MD` – primary operating manual.
2. `.codex/manifest.yaml` – initiative timeline, guardrails, checkpoints.
3. `.codex/agent_roles.yaml` – responsibilities, allowed paths, approval gates.
4. `.kiro/specs/rag-2.0-enhancement/tasks.md` – active implementation plan for RAG 2.0.
5. `.kiro/specs/knowledge-graph-consolidation/tasks.md` – reference plan for consolidation hand-offs.

This ensures every agent inherits the same context, guardrails, and task state. Update this file if new core documents must preload.

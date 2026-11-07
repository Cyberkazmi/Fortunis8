# Architect Handoff Deck Skill

This repository includes the reusable `architect-handoff-deck` skill at `docs/skills/architect-handoff-deck/SKILL.md`.

## Purpose

Use the skill when documenting a completed implementation phase for system architects, product owners, database owners, or technical reviewers. It standardizes evidence collection, written handoff structure, Slides deck creation, security/migration boundaries, and production-gate reporting.

## Team installation

Share the packaged `architect-handoff-deck.skill` archive with team members. Add it to the Manus user skills directory through the team’s normal skill-install flow. The repository copy is the reviewable source-of-truth version and should be updated alongside intentional workflow changes.

## Repository usage

Start from the active branch and current commit. Gather executable evidence before writing claims. Keep the handoff explicit about what is implemented, verified, preview-only, source-only, in memory, or still blocked on production approval. Use the Slides MCP workflow for presentation deliverables and finish with the Slides completion gate.

## Scope guardrails

The skill does not authorize live database migrations, production deployment, payment actions, credential access, branch changes, or public publication. Those operations still require the project-specific approvals and tools described by the task.

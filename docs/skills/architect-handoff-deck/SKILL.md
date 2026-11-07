---
name: architect-handoff-deck
description: Create evidence-led architect handoff reports and presentation decks for completed software implementation phases. Use when summarizing a repository milestone for system architects, product owners, database owners, or technical reviewers, especially when the work includes API/security changes, migrations, frontend integration, tests, deployment boundaries, or explicit production gates.
---

# Architect Handoff Deck

Use this skill to convert a verified implementation checkpoint into a concise, decision-ready architect handoff and presentation. Treat the repository and executed checks as the source of truth. Never turn intended work, mock behavior, or planned migrations into completed functionality.

## Operating principles

- Separate **implemented**, **verified**, **source-only**, and **remaining** work.
- Report exact branches, commit SHAs, test counts, build results, route results, and environment boundaries.
- Preserve repository controls: inspect the active branch first; do not switch protected branches or publish unless explicitly authorized.
- Treat migrations as source artifacts unless execution against the intended database is explicitly authorized. State exactly where validation occurred.
- Never expose secrets, service-role values, tokens, or private credentials in reports or slides.
- Prefer small, verifiable increments over broad rewrites.
- Use the Slides skill and Slides MCP for any presentation. Do not hand-build a standalone deck outside Slides.

## Workflow

### 1. Establish scope and evidence

Inspect the active branch, current commit, remotes, working-tree state, project handoff/report files, and the relevant implementation files. Read existing tests before describing behavior. Identify the checkpoint being documented.

Create an evidence table with these columns:

| Area | Claim | Evidence | Status | Boundary |
|---|---|---|---|---|
| API | Exact endpoint or behavior | Test, route check, or source path | implemented / verified / planned | local, preview, or production |
| Security | Identity and ownership rule | Test or source path | verified | secret/config dependency |
| Data | Migration or repository behavior | SQL comparison/local DB check | source-only / verified | live DB untouched or applied |
| Frontend | Route and state | Build or HTTP check | verified / preview | auth/config dependency |
| Operations | Deployment, notifications, payments | Existing run or explicit absence | remaining | owner/action |

Do not infer evidence from filenames alone. If a check was not executed, label it unverified.

### 2. Produce or update the written handoff

Use an executive summary followed by current phase, completed capabilities, architecture, API/security contract, persistence/migration state, validation evidence, and remaining production gates. Include repository and protected branch status, exact final commit SHA(s), current phase, intentional in-memory/mock/preview/source-only boundaries, exact test/build/route results, an owner/action for each production blocker, and a narrow recommended next increment.

Use full paragraphs plus compact tables where exact values matter. Avoid claiming “production-ready” unless production checks and approvals actually exist.

### 3. Build the presentation

Initialize one Slides deck with the complete outline before authoring pages. Unless the user requests another format, use the available Slides mode and keep the deck to 6–12 slides. For an architect handoff, use this adaptable nine-slide sequence:

1. Cover — phase, checkpoint, branch, date.
2. Executive summary — what changed and what the checkpoint proves.
3. System flow — end-to-end authenticated or data flow.
4. Security/ownership — derived identity, trust boundaries, failure behavior.
5. Persistence/migrations — adapters, schema state, RLS, and execution boundary.
6. Connected product surfaces — API/frontend route matrix and user-visible states.
7. Validation evidence — exact counts and checks.
8. Production gates — timeline or owner/action sequence for remaining work.
9. Architect decision frame — recommended baseline, handoff identifiers, and next approval.

Adapt or remove slides when the project is smaller, but retain the distinction between evidence and future work.

### 4. Use a restrained technical visual system

For architect-facing decks, prefer a whitespace-first editorial report style: strong serif headings, legible sans-serif body text, thin rules, sparse technical diagrams, and no decorative stock imagery. Use a consistent palette with a dark primary, one structural blue, one restrained accent, a pale background, and subtle dividers. Avoid dense dashboards, fake charts, gradients, shadows, rounded UI cards, or invented metrics.

For HTML Slides mode, follow the Slides HTML syntax rules: one complete standalone HTML document per registered slide, fixed 1280×720 canvas, native inline CSS, no unsupported external assets, no animations, and no overflow. Write each slide through the native Slides file tool and finish with `slides/present`.

### 5. Validate the deck and handoff

Before delivery, confirm every registered slide is authored and `slides/present` succeeds; compare all numbers and claims against the evidence table; ensure page titles, branch, commits, and dates are consistent; remove secrets and unverified production claims; verify remaining gates name an owner and concrete action; and deliver one Slides resource link rather than duplicate slide files.

## Recommended claim language

Use “Implemented and verified locally” when tests or route checks prove it; “Source artifact committed; not applied to live database” for unapplied migrations; “Preview route exists; integration remains” for UI surfaces without production data; and “Remaining production gate” for secrets, live migrations, payments, notifications, or deployment approval.

Avoid “Fully integrated” when repositories are in memory, “Secure” without stating what was verified and what remains configured, and “Production-ready” when owner approval, live service validation, or operational systems are absent.

## Recommended final response

State that the handoff deck is complete, link the Slides resource exactly once, summarize the documented checkpoint in 2–4 sentences, and mention the most important remaining production gate. If requested, also provide the written handoff file; otherwise do not duplicate the entire deck in chat.

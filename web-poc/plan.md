# Fortunis8 Hybrid POC Plan

## Scope

This isolated Webdev-managed project proves the smallest useful hybrid deployment shape for Fortunis8 without touching the existing GitHub repository, Telegram bot, Supabase, OpenAI, production credentials, or production data.

Baseline reference: `main @ 518a92f5bd6f84c184cacd9e523f8fea9fb62a65`.

## Architecture

- `frontend/`: Vite-built React single-page frontend.
- `backend/`: Python/FastAPI application with a credential-free `/health` endpoint.
- `public/`: static route manifest required by Webdev.
- `Dockerfile`: production backend container contract for Webdev server deployment.
- Webdev publication shape, prepared but not published: static build for React output, server deployment for FastAPI, and route splitting with `/health` directed to the server and the SPA directed to static output.
- Preview shape: FastAPI serves the built React output and `/health` on the configured port so one process demonstrates browser-to-backend connectivity.

## Design direction

Chosen direction: **Compact mobile command deck** — information-forward, tactile cards, strong status signals, optimized for one-handed use.

- Design movement: compact mobile command deck with editorial mysticism.
- Core principles: immediate status, one-thumb reach, calm hierarchy, honest system state.
- Color philosophy: ink navy provides focus; warm parchment gives the interface a human reading surface; electric saffron marks active intent; mint confirms a live connection.
- Layout paradigm: a narrow reading rail rather than a centered marketing grid; the status card is the first actionable surface.
- Signature elements: constellation-like dot field, pill-shaped connection status, and one elevated action card.
- Interaction philosophy: every action reports what happened; failure states remain useful and retryable.
- Animation: short ease-out entrance only; no decorative motion is required for the POC.
- Typography: system sans stack for compact legibility with a serif display accent for the Fortunis8 wordmark.

## Acceptance boundary

The POC is complete only when the React build, FastAPI startup, `/health` response, browser-facing success state, browser-facing error/retry state, route manifest, existing Python tests, and isolated project checkpoint are all evidenced. Public publication and production integration are explicitly out of scope.

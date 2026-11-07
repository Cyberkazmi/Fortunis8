# Fortunis8 Hybrid POC TODO

## POC frontend and backend

- [x] Build a mobile-first React landing page in the isolated Webdev project.
- [x] Expose a credential-free Python/FastAPI `/health` endpoint.
- [x] Show a clear successful backend connection state in the frontend.
- [x] Show a clear backend connection error state with a user-triggered retry action.
- [x] Keep the project independent of the existing Fortunis8 repository, Telegram bot, Supabase, OpenAI, credentials, and production data.

## Hybrid deployment contract

- [x] Add a self-contained static frontend build contract with verified `dist/index.html` output.
- [x] Add a server deployment contract with a committed Dockerfile and unauthenticated health path.
- [x] Add path splitting for `/health` to the server and the SPA to static output.
- [x] Keep public publication and production configuration unchanged.

## Consumer-facing visual v0

- [x] Replace the technical connectivity screen at `/` with a consumer-facing Fortunis8 landing page.
- [x] Add a separate `/dashboard` product preview with mock persona, zodiac, insight, diamonds, streak, quests, history, and reading entry points.
- [x] Preserve the connectivity test at `/technical-poc` as an internal technical route.
- [x] Capture mobile and desktop landing/dashboard previews for visual approval.
- [ ] Add real login/signup, authenticated API calls, Supabase persistence, OpenAI readings, and server-authoritative rewards only after v0 approval.

## Schema design checkpoint

- [x] Document the multi-belief user profile structure and explicit consent boundaries.
- [x] Draft normalized tables for goals, guidance modes, rituals, assignments, activity, quests, XP, diamonds, unlocks, and notifications.
- [x] Preserve Telegram-first identity while adding a future `auth_user_id` bridge for web SaaS.
- [x] Define catalog-first recommendation flow and versioned ritual assignments.
- [x] Define timezone-aware notification preferences and delivery audit records.
- [ ] Review and approve the schema before executing any migration.
- [ ] Implement migrations, RLS, APIs, scheduler, and integration tests only after schema approval.

## Explicitly deferred

- [ ] Run an actual container build/start: no Docker or Podman runtime is available in this sandbox.
- [ ] Publish publicly: deliberately not requested; Webdev auto-publish is disabled.
- [ ] Execute the SQL draft against Supabase or any production database.

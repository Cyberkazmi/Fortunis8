# Fortunis8 MVP staging smoke test

## Purpose and safety

Run this procedure only against an authorized staging environment with a dedicated Telegram bot, non-production OpenAI credentials, and a disposable Supabase project or schema. Never paste token values into chat, logs, commits, screenshots, or issue comments. Do not use a production bot or production user data for this test.

The procedure validates the implemented MVP journey. The repository's automated tests use mocks and do not replace these external checks. Record the deployment commit SHA, environment name, operator, start/end time, and pass/fail result for each step.

## Prerequisites

Deploy the exact candidate commit and apply `fortunis8_mvp_schema.sql` to the authorized staging database. Configure `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, and `APP_ENV=staging` through the deployment platform's secret manager. Confirm that the bot token belongs to the staging bot and that the Supabase project is disposable or backed up.

Install the declared dependencies with `pip install -r requirements.txt`. Confirm the deployment reports the expected commit SHA and that the process can reach Telegram, OpenAI, and Supabase from the staging network.

## Procedure

### 1. Startup and readiness

Start the application using the deployment's normal process. Confirm startup completes without a configuration traceback and that the process remains healthy. Query the API from an authorized network:

```bash
curl -fsS https://STAGING_HOST/health
curl -fsS https://STAGING_HOST/ready
```

Expected results are `{"status":"ok"}` from `/health` and `{"status":"ready"}` from `/ready` when the staging Telegram configuration is present. Confirm no response or log contains a secret value.

### 2. Telegram onboarding

From a dedicated staging Telegram account, send `/start`. Confirm the bot replies with the default persona, balanced mood, and available commands. Verify that a corresponding row is created in `profiles` with the staging user's Telegram ID, default persona, balanced mood, zero diamonds, and level 1.

Send `/personalize`, choose `Moon Reader`, then choose `hopeful`. Confirm the bot acknowledges both selections and returns an aligned reading. Verify the profile row contains the selected persona and mood after the interaction.

### 3. Reading flows

Send `/fortune`, `/tarot`, and `/horoscope aries`. Confirm each command returns a non-empty response from the staging OpenAI integration and that the bot remains responsive between requests. Send natural-language equivalents such as `tell me my fortune`, `draw tarot`, and `show my profile`; confirm they route to the expected handlers.

If reading history and reward persistence are enabled in the staging build, verify the corresponding `fortune_readings` and `rewards` rows. If they are not enabled by the deployed implementation, record that as an unresolved product gap rather than treating the response alone as persistence verification.

### 4. Quest flow

Send `/quests`. Confirm the bot lists the user's active quests. Complete the `Daily Fortune` quest through the supported staging interaction or service path, then confirm the response reports completion and the expected diamond reward. Repeating the same completion should report that the quest is already complete and must not award the diamonds a second time.

Verify the quest status and profile balance in Supabase. If staging is intentionally configured without Supabase credentials, confirm the local fallback response instead and record that persistence was not tested.

### 5. Streak and reward flow

Run the application's supported daily-reward or streak entry point on two controlled test dates, or use the project's test clock mechanism if one is provided. Confirm the first claim awards diamonds, a repeated same-day claim awards zero additional diamonds, and a consecutive-day claim increments the streak. Verify the resulting balance, level, and streak values in the staging profile.

The current repository contains streak calculation logic but does not expose a complete Telegram command path for applying it. If no staging entry point exists, mark this step **blocked by missing product wiring** rather than claiming it passed.

### 6. External-service failure behavior

In staging only, temporarily use an invalid or revoked OpenAI credential through the secret manager, restart the service, and request `/fortune`. Confirm the bot returns a safe retry message and does not expose the upstream exception or credential. Restore the valid staging credential afterward.

Temporarily make Supabase unavailable or remove its staging configuration. Confirm profile and quest operations use the documented local fallback without crashing the Telegram handler. Restore the database configuration and verify normal persistence resumes.

### 7. Recovery and cleanup

Restore all staging secrets, restart the service, and repeat `/health`, `/ready`, `/start`, and one reading request. Delete the disposable staging profile and test rows if policy permits. Record any logs or screenshots only after removing Telegram IDs, tokens, URLs containing credentials, and user content that should not be retained.

## Exit criteria

The smoke test is **Ready for controlled beta** only when startup, readiness, Telegram onboarding, persona/mood persistence, representative AI reading, quest behavior, and failure recovery pass in staging, and the streak step is either verified or explicitly accepted as a documented product limitation. Automated CI must also be green on both Python 3.10 and 3.11 for the exact deployed commit.

If credentials, a staging bot, or an authorized database are unavailable, the result is **Blocked pending external access**. The repository's mocked tests and CI results do not constitute a live Telegram, OpenAI, or Supabase smoke test.

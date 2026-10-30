# Session API Settings Implementation Plan

> Use superpowers:subagent-driven-development; implement each owned task with meaningful RED→GREEN checks.

**Goal:** Each visitor can configure their own DeepSeek API from an independent UI without sharing credentials.

**Architecture:** Pure config/factory accept an explicit frozen settings object. A Streamlit session adapter owns one immutable snapshot; all UI routes and background factories use it. Connection settings UI handles save, clear, bounded test and navigation.

**Spec:** docs/superpowers/specs/2026-10-30-session-api-settings-design.md

**Constraints:** No shared credential persistence, no implicit webpage .env fallback, no new arbitrary hosts, no secrets in repr/exports/errors, keep existing consent and budgets.

### 1. Pure configuration and connection check

- [x] Add tests for explicit overrides, hidden repr, no global fallback and one-request error-normalized connection testing.
- [x] Implement ConnectionSettings and validation/readiness helpers in config.py; make_gateway(settings=...) bypasses local loading, omitted settings preserves CLI behavior.
- [x] Add bounded test helper, run relevant config/model tests.

### 2. Session adapter and request-path integration

- [x] Add failing tests for isolated session settings, invalidation, retained reports and worker snapshots.
- [x] Add session_connection.py helpers; update observation_ui.py/personality_ui.py to use captured explicit configs, keeping existing factory patch boundaries for tests.
- [x] Run affected observation/personality regressions.

### 3. Settings UI and root route

- [x] Add AppTest for empty visitor state despite local config, save/clear/return, password clearing and no request on save.
- [x] Add independent api_settings_ui.py; sidebar and chat setup links; root reads session readiness and creates explicit gateway.
- [x] Update prior UI fixtures to explicitly seed session credentials for UI checks.

### 4. Review and delivery

- [x] Cross-review all web requests and pending jobs; run full suite and bounded real API checks.
- [x] Inspect actual page/password input/screenshot, update docs and source-only GitHub commit with expected SHA.

### User follow-up: observation setup → chat

- [x] Route final observation confirmation to current chat; preserve settings/report management and existing auto thresholds.
- [x] Add manual/auto root AppTest regressions: usable composer, retained domains/mode, zero requests on empty-chat handoff.

Validation: 388 passed in53.01s; check_data valid true. Actual API verification: one synthetic connection check plus one synthetic chat, 4 total requests. Browser checks confirmed password input empty after save/clear; source-only publication excludes secrets and screenshots.

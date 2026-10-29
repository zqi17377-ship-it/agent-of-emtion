# v0.5 guided-flow development ledger

Plan/spec: docs/superpowers/specs/2026-10-30-guided-flows-design.md. User explicitly requested step-by-step pages, encapsulated features and progress indicators.

- Ruling: implement Streamlit routed steps in existing app, no platform migration. Default first screen is a feature home; each active route shows only its current step. No additional approval question because the interaction direction is explicitly specified.
- Ruling: add conversation-scoped ExplorationState.flows for durable drafts, not widget-only state. Complete version and relationship identity continue to isolate questionnaires.
- Root owns shared flow helpers, routing, chat preparation and integration. Parallel implementers own questionnaires, observation settings and personality pages separately.
- Keep consent, topic restrictions, finite background budgets and correction tombstones. Do not invoke actual model APIs for visual/flow tests.

- Implemented shared step headers, durable research/API consent helpers, a three-entry home, three-step chat preparation, isolated feature routes, single-question questionnaires and separate review/result pages. Drafts live in conversation-scoped flow state and remain isolated by complete version and relationship identity.
- Observation setup has five sequential screens; actual mode changes only at final confirmation. Settings, relation management, per-message annotation and reports use separate pages. MBTI local questions and self-confirmation are also sequential and separate from analysis/results.
- Reviewed return navigation and revocation. Reproduced a stale chat-setup return target, added a failing regression, then centralized setup entry/reset and cleared the return target on exit. Reproduced combined relation/annotation form, added two failing regressions, then split the pages and verified empty-state guidance.
- Final fresh full suite: `python -m pytest -q` → 313 passed in 39.03s, exit 0. `python -m scripts.check_data` → valid true, errors empty. Focused observation tests: 13 passed. No model API calls this iteration.
- Real-browser verification: three-question SWLS midpoint answers produce 12/21 after a separate review; previous navigation restores answers; IPIP50 shows one question and remaining 50; chat setup and observation setup expose only the active step. Observation manual setup showed request count 0/6. Screenshots saved locally under docs/screenshots (excluded from publishing).
- Research limits, request ledgers, topic scopes and original data sources retained. These checks establish application behavior, not clinical or psychometric validity. No new dependencies or public deployment.

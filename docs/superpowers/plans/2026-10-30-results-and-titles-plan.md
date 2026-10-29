# 对话命名与测验展示 Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development to implement each independent task with tests first.

**Goal:** User names persist; options show directly; scored results include matching interpretation and graphics.

**Architecture:** Conversation owns naming state. Questionnaire renderer owns single-question inputs. A separate pure result presentation module derives descriptions and SVG from Questionnaire/QuestionnaireResult; UI and export share it.

**Tech Stack:** Existing Python/Streamlit, SVG, pytest/AppTest; no new dependencies required.

**Spec:** docs/superpowers/specs/2026-10-30-results-and-titles-design.md

## Global Constraints

- API-only product remains; local scoring/graphics do not automatically transmit answers.
- Preserve raw scoring, version/relationship identity, consent and finite budgets.
- Graph positions are within the raw range, not clinical probability or population percentiles.

## Review Focus

- A reply after manual rename must preserve the name.
- A cleared/replaced conversation must not inherit another custom name.
- A new single-choice question must remain unanswered until chosen; back restores prior answer.
- Scores from different lengths/ranges must use each dimension's actual endpoints.
- Single-dimensional well-being tools must not produce unsupported personality labels.

### Task 1: Conversation titles

Files: support_agent/conversations.py, support_agent/ui.py; tests/test_conversation_titles.py.

- [x] Add failing tests for rename persistence, isolation, validation and UI save/cancel without API.
- [x] Implement custom-title state and rename-by-ID with bounded text; add a focused rename form.
- [x] Run targeted tests and review safe rendering/migration.

### Task 2: Visible answer options

Files: support_agent/questionnaire_ui.py and affected questionnaire UI tests.

- [x] Change tests to expect one unanswered radio and visible options; witness failure.
- [x] Replace question and relationship dropdowns with radios, preserve stable keys/drafts and no default.
- [x] Check back/review/version isolation and 50-item single-question rendering.

### Task 3: Result interpretation and graphics

Files: support_agent/survey_presentation.py (new), tests/test_survey_presentation.py; integrate questionnaire result UI/export after Task 2.

- [x] Verify source direction meanings; test low/middle/high inputs, dimensions and scale normalization first.
- [x] Implement pure presentation API returning chart SVG and markdown interpretation; escape text and use accessible labels.
- [x] Use radar for five big-five dimensions, suitable range charts for others; keep raw scores visible and labels accurate.
- [x] Integrate into result page and explicit export, then run complete tests and real browser.

### Task 4: Delivery

- [x] Update README/release and execution evidence, capture actual UI.
- Publication follows these pre-publication checks; the GitHub commit and final delivery record are the evidence of remote publication.

# v0.5.1 API-only development ledger

- Explicit user request: remove offline demonstration; use real API for model and end-to-end verification. The requested behavior is complete enough to implement directly. Retain existing Streamlit project and sequential flows.
- Product factory creates DeepSeek by default and rejects live=False; deterministic gateway moved entirely to tests. CLI/evaluation have no --mock path. Evaluation uses explicit synthetic-only cases and bounded request attempts.
- Root implemented two-screen chat setup, live conversation defaults, mandatory research/API/readiness checks and legacy demo history protection. Backend and documentation were delegated separately and reviewed across ownership boundaries.
- RED→GREEN: default API UI/no mode choice; missing configuration disables chat; legacy workspace history cannot send; old single-chat state cannot be relabelled as live; factory/CLI/evaluation request limits.
- Final complete pytest: 322 passed in 44.90s, exit 0. Data check: valid true, no errors. Real browser sent one fixed adult synthetic case through configured DeepSeek; result status ok, listen action, no error, 3 requests, 5042 ms, reported 3708 input / 201 output tokens. Observation mode remained off. No real user health materials, credential output or API-effect claims based on test doubles.
- Local server restarted with API-only code. Current README, walkthrough and release notes updated; historical release records retained as historical. Publication excludes .env, runtime reports, screenshots and sessions.

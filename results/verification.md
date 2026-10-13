# Week 1 verification

Passed in this environment:
- Python compilation for the server, testers, and tests.
- Local HTTP server returns the shop page (in-process smoke check).
- 3 infrastructure unit tests: URL allowlist; unlisted actions rejected; bug claims remain pending.
- Shop JavaScript checks: case-insensitive/trimmed search, empty search results, cart quantities, arithmetic totals, invalid quantity handling, removal, successful checkout state, and empty-cart rejection.

Not verified:
- Real Chromium workflows and screenshots: Chromium and headless-shell downloads returned invalid/incomplete archives in this environment. The browser smoke is explicitly skipped, not counted as passed.
- Native browser email validation and visual layout.
- Real AI model decisions or bug detection: no API key available, and model/library choices still require trainer review.

Offline fixed-decision and mocked-browser checks are infrastructure checks only. They are not AI evaluation results. No evaluation bugs have been planted, no claimed model advantage has been measured, and no authoring time has been fabricated.

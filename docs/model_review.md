# Week 1 technology choices — for trainer review
Proposed model: OpenAI gpt-4.1-mini-2025-04-14 (fixed snapshot), temperature 0.2. A small instruction-following model is enough to begin this constrained task; no claim of optimality.
Browser automation: Python Playwright 1.63.0 with Chromium; OpenAI SDK 3.26.0. Exact tested dependency versions are recorded in results/environment.json and requirements-lock.txt when available. Browser: page accessibility structure and visible text; screenshots for evidence, not model input.
Actions: click/fill/press by exact accessible role and name; only the local shop origin is permitted. No source inspection, arbitrary code execution, or live-site browsing.
Limits: 30 model decisions and 300 seconds per task; model calls use the remaining time budget. Responses API store=False; only synthetic visible data is sent to the remote API. Browser/website are local; model inference is remote and requires an API key and separate API billing.
Status: choices proposed, NOT yet trainer-reviewed. Main experiments must wait for trainer review. Offline smoke runs test infrastructure only and are not AI results.
Sources:
https://developers.openai.com/api/docs/models/gpt-4.1-mini
https://developers.openai.com/api/docs/guides/structured-outputs
https://playwright.dev/python/docs/aria-snapshots
https://playwright.dev/python/docs/library

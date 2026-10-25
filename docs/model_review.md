# Gemini replacement model

Provider: Google Gemini Developer API using a locally set GEMINI_API_KEY. Default model: gemini-3.5-flash-lite. This model is currently listed with a free tier; actual access, billing and quotas depend on the trainer's project. No Vertex AI setup or Google Cloud login is attempted. No key is included in source files.

Browser: Playwright 1.63.0 / Chromium. Reads accessible structure; keeps screenshots as evidence. Local browser requests and the existing action allowlist are unchanged. Search and cart outcomes are verified against observed page state. This change does not make an AI claim proof of success.

The adapter uses the Generate Content REST endpoint, JSON-schema output, and local Pydantic validation. It records the configured model, returned model version, request ID, and usage counts. Invalid, blocked or truncated responses execute no action. HTTP 429 is recorded as rate_limited; a safe retry delay is recorded when supplied. No automatic fallback or retries. The program cannot determine the key's billing plan, so the key owner must keep its project on a free plan for zero spending.

The earlier Groq and initial OpenAI results remain historical evidence. New Gemini runs are a separate development condition; do not blend model results. Keep the same tasks and freeze the selected provider/model/settings before the trainer plants final bugs. No artificial defects are introduced by this migration.

References checked for this update:
https://ai.google.dev/gemini-api/docs/pricing
https://ai.google.dev/gemini-api/docs/deprecations
https://ai.google.dev/gemini-api/docs/generate-content/structured-output
https://ai.google.dev/api/generate-content

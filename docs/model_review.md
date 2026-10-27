# Gemini replacement model

Provider: Google Vertex AI express mode. Model: `gemini-3.5-flash-lite`, matching config.json and the trainer's endpoint/model correction on 2026-10-25. Authentication: locally set GEMINI_API_KEY sent only in x-goog-api-key.

Endpoint: https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:generateContent

Playwright 1.63.0 / Chromium reads accessible page structure and retains screenshots. Browser requests remain restricted to the local synthetic shop. Search and cart outcomes require independent page-state verification.

Generate Content REST requests use JSON-schema output and strict local Pydantic validation. No SDK, automatic model fallback, retry or billing change is introduced. The trainer controls account access, free allowance and billing; the program cannot establish them from the key. Request spacing is 1 second between starts, with actual waiting recorded separately from API duration and execution. Task wall time remains capped at 300 seconds including waits.

HTTP status, retry delay and a sanitized Google ErrorInfo reason code are retained, including on failed requests. Raw error messages/bodies and keys are not logged. No live Vertex run has been verified here. Keep Vertex development results separate from historical Groq runs.

Reference: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/express-mode/vertex-ai-express-mode-api-reference

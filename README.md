# AI Website Tester — Gemini edition

A small local synthetic shop, four scripted browser tasks, and an AI agent that chooses browser actions from accessible page structure. No deliberately planted bugs are included yet. This is a programming project to run on your computer, not a hosted website.

## Start on Windows (VS Code terminal / PowerShell)
1. Extract this folder, open it in VS Code, and open a terminal in the project folder.
2. Run:
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe serve.py
```
3. Open http://127.0.0.1:8000 in your browser. Keep that terminal running.
4. In a second terminal, run:
```powershell
.\.venv\Scripts\python.exe -m tester.scripted
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
Scripted reports, screenshots, and traces go under `results/runs/`. A failed check is a candidate requiring manual reproduction, not automatically a confirmed bug. `python -m playwright show-trace PATH` opens a trace.

## AI setup — Vertex AI express mode
The active provider is now **Google Gemini**, default model `gemini-3.5-flash-lite`. This uses the Vertex AI express-mode endpoint with an express-mode key in the `x-goog-api-key` header. If your trainer specifies another accessible Gemini model, update `model` in config.json before running. Record that change for the experiment.

No review flag is required. The adapter uses Python's standard library; your existing installed project dependencies are sufficient. Existing Groq adapter tests are retained as historical regression checks, but the agent never falls back to Groq or OpenAI.

1. Keep the local shop running in one terminal.
2. In a second PowerShell terminal, set the Gemini key locally:

```powershell
$env:GEMINI_API_KEY = 'YOUR_GEMINI_KEY'
.\.venv\Scripts\python.exe -m tester.agent --task cart --repeats 1
```

Never put the real key in source files, commits, or chat. `.env` is ignored but not automatically loaded. If a credential was disclosed, use a replacement from its owner. Do not reuse `GROQ_API_KEY` for a Gemini key.

Reports are saved under `results/runs/ai-gemini-.../run-1/cart/`. The search and cart verifiers still check actual UI outcomes. `finished` alone is not a passing result. Other tasks still need independent checks or manual verification.

Gemini has its own per-project rate and quota limits; changing provider does not guarantee uninterrupted runs. The code sends one request at a time, spaces requests according to config.json (1 second between request starts by default), and stops on a quota error. It does not automatically retry, change model, enable billing, or use a paid fallback. **Billing depends on the trainer's Google project**: a model with a free tier is not proof that every key uses the free tier. The trainer must confirm the key remains within its free allowance if spending must be zero.

The browser visits only the local synthetic shop; the model request goes to Google's remote API and contains synthetic visible text. No database access is used. Do not compare Gemini development timings directly with earlier Groq timings as if they were the same model. Freeze one provider/model/config before the final blind evaluation.

## What is ready
- Search, quantity changes, cart totals, remove-item, and simulated checkout.
- Shared requirements, four task descriptions, initial scripts, and initial AI instructions written before bug planting.
- Structured model decisions; only click/fill/press permitted; loopback-only browser requests.
- Step/time limits; screenshots, observations, actions, token usage, incomplete-run status, and pending bug claims.
- Effort CSV and prewritten scoring rules. Log YOUR active time from now; no historical authoring time has been invented.

## What has NOT happened
Live Gemini inference has not been verified in this environment; no blind evaluation and no bug-detection claims. Offline agent tests use fixed decisions solely to test browser/report plumbing.

## Next stages
1. Trainer reviews tools; run one AI development task on the healthy shop.
2. Confirm scoring and initial requirements; retain this initial version before own development bugs.
3. Develop using own bugs, recording writing/update time for both approaches.
4. Freeze scripts, prompts, model/config, task requirements, and agent code (use `python freeze.py`).
5. Trainer creates final hidden variants. Do not inspect their implementation or tune testers against results.
6. Run frozen testers from resets, verify claims, and compute quality AND effort comparisons.

`docs/scoring.md` defines planted matching, duplicates, unexpected real bugs, false claims, and infrastructure failures. Model completion claims do not prove task completion; independently validate outcomes.

## Timing and provider diagnostics
Reports retain wall-clock `elapsed_seconds` and add `timing.request_wait_seconds`, `api_request_seconds`, `api_requests`, and `execution_seconds_excluding_request_wait`. Execution includes browser work, screenshots, model response latency and report preparation; it is not CPU time or human authoring time. Waiting is measured, including before a failed API request. The 300-second task budget still includes waiting. Google ErrorInfo reason codes (for example SERVICE_DISABLED) appear in the console error and report `reason_code`; raw error bodies and credentials are excluded.

Record human writing and updating time separately in docs/effort_log.csv. Start a timer before editing scripts or AI instructions and stop when done; split categories and exclude breaks. Leave unknown historical times blank rather than estimate them as measured. Freeze provider, model, prompt and configuration before blind evaluation.

## All four task completion checks
Quantity and checkout now require independent checks of executed actions and observed page results. See docs/quantity_checkout_verification.md. Existing historical reports are preserved. Extra evidence screenshots count toward execution time.

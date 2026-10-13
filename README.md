# AI Website Tester — week 1 starter

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

## AI setup — after trainer review
Send `docs/trainer_message.txt` and `docs/model_review.md` to your trainer. After review, set `trainer_reviewed` to `true` in `config.json`. API inference is remote; the shop and browser remain local. A ChatGPT subscription is not an API credential or API credit.

Set your own API key locally in PowerShell (do not commit it or send it in chat), then run:
```powershell
$env:OPENAI_API_KEY = 'YOUR_API_KEY'
.\.venv\Scripts\python.exe -m tester.agent --repeats 1
```
This is a DEVELOPMENT run. After freezing the testers and receiving trainer-planted evaluation variants, use `--repeats 5`. API calls may incur charges. Start with one run, check usage, and agree a budget with your trainer. The key is never included in reports.

## What is ready
- Search, quantity changes, cart totals, remove-item, and simulated checkout.
- Shared requirements, four task descriptions, initial scripts, and initial AI instructions written before bug planting.
- Structured model decisions; only click/fill/press permitted; loopback-only browser requests.
- Step/time limits; screenshots, observations, actions, token usage, incomplete-run status, and pending bug claims.
- Effort CSV and prewritten scoring rules. Log YOUR active time from now; no historical authoring time has been invented.

## What has NOT happened
No real-model AI run without a key; no main experiments before trainer review; no blind evaluation and no bug-detection claims. Offline agent tests use fixed decisions solely to test browser/report plumbing.

## Next stages
1. Trainer reviews tools; run one AI development task on the healthy shop.
2. Confirm scoring and initial requirements; retain this initial version before own development bugs.
3. Develop using own bugs, recording writing/update time for both approaches.
4. Freeze scripts, prompts, model/config, task requirements, and agent code (use `python freeze.py`).
5. Trainer creates final hidden variants. Do not inspect their implementation or tune testers against results.
6. Run frozen testers from resets, verify claims, and compute quality AND effort comparisons.

`docs/scoring.md` defines planted matching, duplicates, unexpected real bugs, false claims, and infrastructure failures. Model completion claims do not prove task completion; independently validate outcomes.

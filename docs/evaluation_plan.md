# Pre-registered evaluation plan

Source baseline: db75ec7067df4c3d7bf0ad58abd5f3eed59851bf. This preparation changes documentation and the freeze utility, not either tester's decision logic. Commit the resulting manifest and documentation and record that preparation commit before sharing with the trainer. No blind bugs have been supplied or scored in the evidence reviewed so far.

## Freeze and scope

Use Gemini gemini-3.5-flash-lite via Vertex AI express, temperature 0.2, maximum 30 model decisions, maximum 300 seconds per AI task including waits, 1-second minimum between request starts, and Playwright 1.63.0. Freeze config.json, dependency versions, tester modules, test code, task requirements, AI instructions, scoring and this plan. Only local synthetic MiniShop browsing is allowed. No databases or live websites. Keys stay in environment variables.

The existing scripted runner has 3-second locator/action timeouts and Playwright's default 5-second assertion timeout. It does not enforce the AI's 300-second whole-task ceiling. Report this difference; do not describe the comparison as equal-time-budget testing. Scripts and AI share task requirements and the same shop revision, but their assertion coverage also differs. Task completion and bug detection are distinct outcomes.

## Fixed runs

Run five full suites per engine on the healthy shop, then five full suites per engine on the trainer's evaluation shop: 4 tasks x 5 repeats x 2 engines per shop condition. A fresh Browser context is created for each task. Run serially; use scripts then AI in each condition. Keep the same provider/model/prompt/configuration and machine. Record actual condition-specific shop commit/hash, preparation commit, environment and returned model versions. No run-until-pass, selective replacement, model swapping, prompt repair or script repair after blind results.

Retain existing development runs separately, including skipped-step failures. Do not merge them into this fixed five-repeat experiment. Preserve raw JSON, screenshots and traces, plus provider and infrastructure failures.

If a rate/quota error aborts a suite, retain the partial repeat, record its ID and label unexecuted tasks as not run. Wait until access returns before the next planned repeat; do not silently restart or replace the aborted repeat. Report per-repeat detections against all planted bugs, including zero detection for unexecuted tasks, together with availability/completion. Do not attribute API errors to the shop. Any extra recovery runs must be clearly exploratory and excluded from the fixed primary analysis.

## Review and scoring

Follow docs/scoring.md. Finish a human review of claims from both engines, with requirement, actual/expected behavior, reproduction steps and evidence. A scripted failed assertion is a candidate, not an automatic confirmed bug; a false independent completion check is also not a bug claim by itself. Document review time separately. Do not use the hidden bug list to invent missing tester reports.

For each repeat, deduplicate reproduced planted bugs across all four tasks and divide by the trainer's total planted defect count. Report five values plus minimum, median and maximum. A bug found in several repeats counts once in each repeat; also report the union across repeats as a separate number. Trainer keeps defect IDs/count/mapping until runs and report drafts are saved.

Review unique claims per repeat as planted, genuine unplanted, false, or pending. Precision = (confirmed planted + confirmed unplanted unique claims) / all unique claims. When there are no claims, precision is N/A. Pending claims stay visible in the denominator and must be resolved before declaring the precision target met. Duplicate reports of the same underlying defect count once per repeat. Report confirmed unplanted defects separately from planted detection; they never change its denominator. Healthy-control confirmed real defects are additional findings, not false alarms; false claims are false alarms. Infrastructure errors and incomplete coverage are separate counts.

Pre-existing targets remain median planted detection >=70% and confirmed-report precision >=90%. Evaluate targets per engine; lower results are valid outcomes. If the trainer supplies zero planted bugs, planted detection is N/A. Report counts with percentages because this is a small study. Do not infer general model superiority from this shop.

## Timing and effort

Report elapsed_seconds, request_wait_seconds, api_request_seconds and execution_seconds_excluding_request_wait separately. API time is included in execution, not added to it again. Extra evidence screenshots count as execution. Script elapsed time is wall time. Report min/median/max by task and suite, including incomplete-run labels rather than implying failures completed faster. Keep token usage separate from authoring effort.

Log actual human script-writing/updating minutes, AI prompt-writing/updating minutes, shared setup, provider integration and report-review minutes separately. Use docs/effort_log.csv. Historical unmeasured values stay blank; missing time limits any claim that AI saved authoring effort. AI-assisted implementation is labeled explicitly; do not treat generated code as unaided student writing.

## Trainer handoff

Give the trainer the preparation commit and docs/requirements.md. Ask for a separate branch/archive containing only changes to shop/index.html, no changes to tester code, config or prompts. The task completion checkers expect existing accessible labels and DOM hooks; keep them intact so the study measures behavior under the stated interface. Other interface mutations require a separately pre-registered study.

The trainer chooses hidden behavioral defects and keeps a private mapping from defect ID to requirement, expected behavior and minimal reproduction. Do not disclose the number, locations or symptoms until raw runs and report drafts are saved. The trainer should independently check the healthy baseline; record any pre-existing defect separately. The student must not inspect the mutated source or diff before testing.

Do not plant evaluation bugs yourself. On receiving the archive, replace only shop/index.html using the trainer's directions and record its SHA-256 without opening it. Verify frozen tester files with --allow-shop-changes. After runs are saved, the trainer/reviewer reproduces reports, matches planted defects and resolves unplanted/false claims.

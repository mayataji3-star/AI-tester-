# Scoring protocol v1 — record before testing
Final evaluation bugs are planted ONLY by the trainer after scripts, prompts, configuration, and agent code are frozen. Own bugs are development only. Do not reveal source or hidden bug lists to the tester.

A finding requires: requirement ID, actual vs expected behaviour, concrete reproduction steps from a fresh state, and a saved screenshot/trace. Another person must reproduce it and the trainer must match it to the planted defect. Failed checks without diagnostic evidence do not automatically count as bugs. The same defect counts once per run; multiple independent defects may count separately. Scoring is symmetric for scripts and AI.

Confirmed unplanted requirement violations are additional real bugs, reported separately; they do not enter the planted detection numerator or denominator. Incorrect/unreproducible claims are false reports. Infrastructure/API/browser errors and exhausted runs are tracked separately, not quietly discarded. Pending reports remain unverified.

Planted detection = unique reproduced planted bugs / total trainer-planted bugs. Report precision = confirmed real unique bugs / all unique bug claims; if no claims, precision is N/A (not 100%). Repeat the full AI suite five times from resets, reporting min/median/max; compare with scripted suite. Report clean-control false alarms. Each task uses the same requirements and a 300-second execution budget. Preserve incomplete runs in results.

Log active authoring, debugging, and maintenance minutes for scripts and AI instructions separately, on the same development tasks; exclude idle time. Record shared setup, AI integration work, and report review separately. Do not invent historical durations. Report quality and effort together; API usage is separate from authoring time.

Targets: median planted detection >=70%; confirmed-report precision >=90%. A result below target remains a valid experiment. No changes after seeing blind evaluation results.

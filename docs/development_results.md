# Development evidence summary — before blind evaluation

Model used for the current AI development results: gemini-3.5-flash-lite via Vertex AI express, request interval 1 second. These are development checks, not a completed final evaluation or evidence of bug detection. No trainer-planted evaluation defects have been scored.

| Task | Evidence reviewed | Result and limits |
|---|---|---|
| Scripted suite | Earlier uploaded Windows screenshots/traces and report | All four tasks passed in that development run; not a new run of the final frozen version. |
| Cart AI | Full report and uploaded development archive | One independently verified pass, 15.807 seconds. Three cart checkpoints confirmed. |
| Search AI initial | Full report | Incomplete: performed HEAD but skipped zzzz while claiming completion, 6.461 seconds. |
| Search AI repeat batch | ai-gemini-20261025-151829, all three reports | Failed / passed / passed, 6.023 / 7.154 / 8.082 seconds. Failure again skipped zzzz. Both passes performed both searches. |
| Quantity AI before independent checker | Full report in latestfile.zip | Manual review supports rejection of 0, -1 and 1.5 and £40 for quantity 2; 15.054 seconds. Original report remains model_claim_only. |
| Quantity AI after checker | Student terminal output only | quantity finished True reported; the new full report has not been independently reviewed here. Retain and include it in the evidence bundle. |
| Checkout AI before independent checker | Pasted text(2).txt | Manual review supports the complete task; 16.125 seconds; original report model_claim_only. |
| Checkout AI after checker initial | Pasted text(3).txt | Failed completion, 14.222 seconds: skipped empty cart with a valid email. Later actions succeeded, but ordered checker requires the missing first checkpoint. |
| Checkout AI latest repeat batch | ai-gemini-20261027-103551, latest-checkout-results.zip | Three independently verified passes: 14.265 / 15.387 / 13.982 seconds. Replayed recorded before/after states through verifier; linked evidence PNGs present. |

Earlier Developer API permission failures and historical Groq quota/false-completion runs remain setup/development history, not part of the fixed final experiment. Keep them; do not substitute them for Vertex repeats.

No supported claim yet about relative bug detection, time saved writing tests or overall reliability. The available effort-log entries leave unmeasured historical human minutes blank. Preserve those gaps honestly and time future human work. The latest updated local unit checks reported 37 passes and one browser smoke skip in the assistant environment; that skip is not a Windows browser failure or a live model result.

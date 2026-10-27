# Independent quantity and checkout verification

Added during development, before the trainer's blind evaluation. Existing run reports retain their original meaning; this change does not relabel historical model-only results.

The runner reads rendered cart state before and after successfully executed actions. Checkout additionally reads the email element's native validity and visible status message. Verifiers never ask the model to judge its own completion, read application variables/source, or choose browser actions. Successful final completion requires both the model's finish flag and every independent checkpoint. Failed browser actions cannot contribute evidence.

Quantity checkpoints: attempt 0, -1 and 1.5 from quantity 1; commit each with Tab/Enter or a click away; each must restore quantity 1 with subtotal and total £20. After all three, commit quantity 2 with subtotal and total £40. Filling a field without committing it is insufficient.

Checkout checkpoints in order: submit an empty cart with a natively valid email and observe the empty-cart message; submit Mouse quantity 1 / £10 with a malformed email, observe native type mismatch and no success or cart clearing; submit with a valid email and observe a new demo-order confirmation, no cart rows and £0. A blank email alone does not prove the empty-cart check.

Reports contain independent_checks, before/after state and after-NN.png evidence. Additional screenshots and UI reads count toward execution time; compare fresh runs using this version rather than mixing their timings with earlier versions. No extra API calls or prompt changes are introduced. Save failed and successful development runs.

Verification labels: verified_quantity_outcomes / verified_checkout_outcomes on a completed, verified run; not_verified otherwise. These check task completion, not whether reported bugs are reproducible. Bug claims remain pending manual reproduction. Current task specifications cover only their listed examples, not every possible invalid value, email or checkout condition.

Before blind evaluation, freeze code, model, configuration, prompts and scoring rules. The trainer supplies evaluation bugs. Start timing your own setup and future script/prompt edits separately in docs/effort_log.csv; do not fabricate unknown historical minutes.

# Phase 19 — OpenCode Implementation Prompt

You are implementing Phase 19 of Saamu Tailors.

Before changing code:
1. Read every file under `docs/phase-19/`.
2. Inspect the current repository and Phases 0–18.
3. Inspect git status and preserve all pre-existing uncommitted work.
4. Verify which reminder/lifecycle capabilities actually exist.
5. Do NOT invent a feature merely because it is listed as a candidate.

Implement only the Phase 19 scope justified by the repository and these documents.

Critical constraints:
- This is a preparation/review reminder workflow.
- Do NOT automatically send WhatsApp/SMS/email.
- Do NOT integrate Meta, Twilio, provider SDKs, webhooks, credentials, or external senders.
- Reuse Phase 18 communication preparation and authoritative payment/order services.
- Preserve OWNER/STAFF RBAC.
- Avoid migrations unless genuinely required and justified.
- Do not expose destructive operations through the browser.
- Do not log full phone numbers or secrets.
- Do not alter unrelated Phase 17/18 work.

Testing:
- Run focused Phase 19 tests.
- Run backend check and migration check.
- Run the full backend suite.
- Run Black/isort.
- Run frontend lint, TypeScript, and build if frontend changed.

Documentation:
- Update the completion report with actual results.
- Leave manual verification NOT STARTED.
- Do not create a git commit unless explicitly requested.

If the documents or repository are insufficient to justify a concrete implementation, STOP and report the ambiguity rather than guessing.

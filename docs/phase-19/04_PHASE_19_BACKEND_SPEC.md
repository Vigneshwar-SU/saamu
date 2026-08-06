# Phase 19 — Backend Specification

Inspect the repository and Phases 0–18 before coding.

Create a focused reminder service only where justified. It should:
- evaluate eligibility;
- return deterministic candidates;
- reuse Phase 18 communication preparation;
- avoid duplicate business calculations;
- expose explicit status/reason codes.

Do not create generic command execution or arbitrary filesystem/network operations.

Tests must cover eligibility, all implemented reminder types, RBAC, invalid inputs, missing phones, Phase 18 message agreement, duplicate prevention, business-data preservation, and privacy.

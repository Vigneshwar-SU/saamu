# Phase 19 — Architecture

## Principle
Build a thin reminder orchestration layer over existing authoritative services.

## Flow
Existing order/payment/customer state → eligibility evaluation → reminder candidate → deterministic Phase 18 message preparation → operator review/action → WhatsApp-ready handoff.

Automatic external delivery is prohibited.

## Source of Truth
Reuse:
- Existing order lifecycle/status rules.
- `Customer.mobile_number`.
- Existing authoritative payment summary.
- Phase 18 templates, phone normalization, and WhatsApp URL construction.

Do not recreate these rules.

## Persistence
Prefer deterministic derivation without new persistence. If idempotency genuinely requires persistence, document and justify it before adding a model/migration.

## Security
Backend-authoritative RBAC; no provider secrets; no full-number logging; no automatic external network delivery.

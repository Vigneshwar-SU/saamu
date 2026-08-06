# Phase 13 — Database Specification

Prefer existing `CustomerPayment` and finance data rather than creating a duplicate Income table.

Use existing payment information such as:
- invoice/order relationship
- amount
- payment type
- payment method
- payment timestamp/date
- refund relationship
- recorded_by

Income totals and breakdowns should be derived rather than independently stored.

Net customer-derived income:
`qualifying customer payments - refunds`

Do not store independently maintained total-income or net-income fields when they can be calculated.

Do not create a migration unless a genuine Phase 13 schema requirement exists. If no schema change is required, migration checks must remain clean.

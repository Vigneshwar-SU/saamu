# Phase 9 — Data Model

## Invoice

| Field | Type | Notes |
|---|---|---|
| order | OneToOne/FK Order | Existing order being billed |
| invoice_number | CharField | Unique, server-generated |
| invoice_date | DateField | Required |
| subtotal | Decimal(12,2) | Derived from invoice items |
| adjustment_amount | Decimal(12,2) | Only if enabled by approved rules |
| total_amount | Decimal(12,2) | Derived |
| notes | TextField | Optional |
| created_by | FK User | Audit |
| timestamps | | TimeStampedModel |

## InvoiceItem

| Field | Type | Notes |
|---|---|---|
| invoice | FK Invoice | Parent |
| garment_type | CharField | Snapshot |
| garment_code | CharField | Snapshot |
| quantity | PositiveInteger | Snapshot |
| unit_price | Decimal(12,2) | Snapshot |
| line_total | Decimal(12,2) | Snapshot |

Invoice items preserve the billing snapshot so later order changes do not rewrite historical invoice presentation.

## CustomerPayment

| Field | Type | Notes |
|---|---|---|
| invoice | FK Invoice | Target invoice |
| amount | Decimal(12,2) | Must be > 0 |
| payment_date | DateField | Required |
| payment_method | CharField | CASH / UPI / BANK_TRANSFER / OTHER |
| reference | CharField | Optional |
| notes | TextField | Optional |
| recorded_by | FK User | Server-side audit |
| timestamps | | TimeStampedModel |

Customer payments are append-only.

## Derived Values
- subtotal = sum(invoice item line totals)
- total = subtotal + approved adjustment
- amount_paid = sum(CustomerPayment.amount)
- balance_due = total - amount_paid
- status = UNPAID when paid = 0
- status = PARTIALLY_PAID when 0 < paid < total
- status = PAID when balance_due = 0

No negative balance is permitted.

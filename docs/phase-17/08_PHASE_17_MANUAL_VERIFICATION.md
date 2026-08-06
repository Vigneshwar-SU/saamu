# Phase 17 — Manual Verification

**Status: NOT STARTED**

Do not mark items complete until a human operator performs them.

## A. Access
- [ ] OWNER can export CSV.
- [ ] OWNER can export PDF.
- [ ] STAFF can export CSV.
- [ ] STAFF can export PDF.
- [ ] Anonymous users cannot access exports.

## B. All-time
- [ ] Export CSV with no range.
- [ ] Export PDF with no range.
- [ ] Compare key figures with Reports.

## C. Filtered exports
- [ ] Apply From date and export both formats.
- [ ] Apply To date and export both formats.
- [ ] Apply both dates and export both formats.
- [ ] Confirm inclusive boundaries.

## D. Content
- [ ] CSV opens correctly in a spreadsheet application.
- [ ] CSV contains expected sections.
- [ ] PDF opens correctly.
- [ ] PDF pages are readable and not clipped.
- [ ] Financial values match Reports.
- [ ] Order/customer/tailor figures match.
- [ ] Income/expense breakdowns match.
- [ ] Refunds are correct.
- [ ] Net position matches.

## E. Errors
- [ ] Invalid date produces a clear error.
- [ ] Reversed range produces a clear error.
- [ ] Failed export leaves Reports usable.

## F. Duplicate-submit
- [ ] Rapid CSV clicks do not create accidental duplicate requests.
- [ ] Rapid PDF clicks do not create accidental duplicate requests.

## G. Security/non-mutation
- [ ] No secrets/tokens appear.
- [ ] No internal stack trace appears.
- [ ] Orders/payments/expenses/customers/tailors/payroll remain unchanged.

## Completion rule
This checklist remains **NOT STARTED** until the operator actually performs it. Automated tests do not count as manual verification.

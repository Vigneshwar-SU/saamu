# Phase 17 — Testing Specification

## Backend

### RBAC
1. Anonymous CSV → 401.
2. Anonymous PDF → 401.
3. OWNER CSV/PDF → 200.
4. STAFF CSV/PDF → 200.
5. POST/PUT/PATCH/DELETE rejected.

### Range validation
6. All-time.
7. `date_from` only.
8. `date_to` only.
9. Combined range.
10. Inclusive boundaries.
11. Invalid dates.
12. Reversed range.

### CSV correctness
13. Required sections exist.
14. Stable headers.
15. Orders/status/garments match the report service.
16. Customer metrics match.
17. Tailor workload matches.
18. Income matches `build_income_summary`.
19. Expenses match `build_expense_summary`.
20. Net position matches authoritative result.
21. Refund/payment-type/expense-category rows are represented.

### PDF correctness
22. Response is a PDF.
23. Title/range are present where extractable.
24. Key financial figures are represented.
25. Major operational sections are represented.
26. PDF generation does not mutate records.

### Safety
27. Safe filename.
28. No secrets.
29. No internal exception leakage.
30. No arbitrary filesystem path.
31. No business-record mutation.

## Regression
Run the full backend suite and ensure Phase 14 report tests remain green.

## Frontend
Run:
```text
npm run lint
npx tsc --noEmit
npm run build
```

If frontend test infrastructure exists, add focused tests for applied-range behavior, pending state, and failure state.

Avoid brittle byte-for-byte PDF snapshots.

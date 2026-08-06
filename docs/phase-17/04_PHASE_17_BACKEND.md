# Phase 17 — Backend Implementation Plan

## Step 1 — Inspect first
Before coding:
1. Read the Phase 14 Reports implementation.
2. Inspect `build_reports_summary`.
3. Inspect finance URL/view conventions.
4. Inspect error handling.
5. Inspect frontend download conventions.
6. Inspect dependencies before adding anything.
7. Establish the existing test baseline.

Do not modify code until inspection is complete.

## Step 2 — Export service

### CSV
Implement deterministic serialization with sections:
1. Metadata
2. Orders
3. Customers
4. Tailor workload
5. Financial summary
6. Income by payment type
7. Expenses by category

Use stable headers/order and UTF-8.

### PDF
Create a clean operational report with title, range, generated timestamp, summaries and tables. Handle page breaks cleanly.

Use an existing suitable dependency if present; otherwise add the smallest justified dependency and document it.

## Step 3 — Views
Implement GET-only export views with:
- `IsOwnerOrStaff`;
- existing `_parse_range` validation;
- inclusive range semantics;
- correct Content-Type;
- safe Content-Disposition filename.

## Step 4 — URLs
Add routes under the existing reports area.

## Step 5 — Tests
Cover:
- anonymous → 401;
- OWNER/STAFF → 200;
- mutation methods → 405;
- all range combinations;
- invalid/reversed ranges → 400;
- CSV structure;
- valid PDF response;
- authoritative totals;
- refunds/expenses/net position;
- no mutation;
- safe filenames;
- no secret/error leakage.

## Step 6 — Gates
Run:
```text
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest <relevant finance tests>
python -m pytest
python -m black --check <touched backend files>
python -m isort --check-only <touched backend files>
```

No migration should be necessary for this feature.

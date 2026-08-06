# Phase 17 — Frontend Implementation Plan

## Reports page
Extend the existing Phase 14 Reports page without redesigning it.

Add:
- `Export CSV`
- `Export PDF`

## Date semantics
Exports use the **applied** report range only.
- Changing inputs without Apply does not change export scope.
- Apply updates export scope.
- Reset makes it all-time.

## UX
While exporting:
- disable the relevant button(s);
- show loading state;
- prevent duplicate requests.

On failure:
- show a clear recoverable error;
- preserve report data;
- allow retry.

On success:
- browser downloads the file;
- no navigation away from Reports.

## Implementation
Inspect `financeService.ts`, React Query hooks, API client, download handling, and UI conventions. Prefer existing helpers.

Do not introduce a large library without justification.

## Gates
```text
npm run lint
npx tsc --noEmit
npm run build
```

Do not calculate authoritative totals in React.

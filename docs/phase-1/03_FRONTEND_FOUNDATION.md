# Frontend Foundation

## Objective
Stabilize React + TypeScript + Vite so it can consistently consume the backend.

## Stack
Use the existing Phase 0 frontend stack and configuration. Do not replace it without a documented reason.

## API Client
Maintain one centralized API client/service layer.

Use an environment-driven variable such as:
```text
VITE_API_BASE_URL
```

Preferred flow:
```text
React component
      |
      v
Service/API client
      |
      v
Axios
      |
      v
/api/v1/
```

Prepare the client for authentication headers/token handling in Phase 2, but do not implement the complete auth flow now.

## Error Handling
Create reusable handling for standardized API errors. Avoid duplicating parsing logic across components.

## Routing
Keep routing functional and ready for authenticated ERP routes. Login may remain a foundation/mock page until Phase 2.

## UI Foundation
Preserve Phase 0 identity:
- Primary `#1E3A8A`
- Secondary `#2563EB`
- Accent `#10B981`
- Background `#F8FAFC`
- Surface `#FFFFFF`
- Error `#EF4444`
- Success `#22C55E`
- Border radius `12px`
- Inter typography
- Clean ERP styling
- Solid surfaces
- Subtle borders/shadows
- No unnecessary glassmorphism

## Quality
These must work:
```text
npm run build
npx tsc --noEmit
npm run lint
```
Only report success when actually executed.

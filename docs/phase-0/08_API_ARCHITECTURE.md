# Saamu Tailors — API Architecture

## 1. Base path

All application APIs should be versioned:

```text
/api/v1/
```

## 2. Authentication

Future endpoints will follow a structure similar to:

```text
/api/v1/auth/login/
/api/v1/auth/refresh/
/api/v1/auth/logout/
/api/v1/auth/me/
```

Exact implementation can be finalized during the authentication phase.

## 3. Customer APIs

Expected resource pattern:

```text
GET    /api/v1/customers/
POST   /api/v1/customers/
GET    /api/v1/customers/{id}/
PATCH  /api/v1/customers/{id}/
```

Additional endpoints should be introduced only when they represent meaningful business operations.

## 4. Order APIs

Expected pattern:

```text
GET    /api/v1/orders/
POST   /api/v1/orders/
GET    /api/v1/orders/{id}/
PATCH  /api/v1/orders/{id}/
```

Workflow operations may use explicit actions where appropriate, for example:

```text
POST /api/v1/orders/{id}/status/
POST /api/v1/orders/{id}/assign-tailor/
POST /api/v1/orders/{id}/collect/
```

Do not blindly expose every database operation as an API.

## 5. Tailor APIs

```text
GET    /api/v1/tailors/
POST   /api/v1/tailors/
GET    /api/v1/tailors/{id}/
PATCH  /api/v1/tailors/{id}/
```

Workload and salary endpoints should represent business operations.

## 6. Payment APIs

```text
GET    /api/v1/payments/
POST   /api/v1/payments/
GET    /api/v1/payments/{id}/
```

Payment creation must validate order/customer relationships and financial constraints.

## 7. Expense APIs

```text
GET    /api/v1/expenses/
POST   /api/v1/expenses/
GET    /api/v1/expenses/{id}/
PATCH  /api/v1/expenses/{id}/
```

## 8. Dashboard APIs

Dashboard endpoints should return calculated information from real data.

Example:

```text
GET /api/v1/dashboard/summary/
GET /api/v1/dashboard/orders/
GET /api/v1/dashboard/financial/
GET /api/v1/dashboard/tailors/
```

Exact endpoint grouping can be refined based on query performance and UI needs.

## 9. Reports

Reports should be query-driven.

Example:

```text
GET /api/v1/reports/income/
GET /api/v1/reports/expenses/
GET /api/v1/reports/orders/
GET /api/v1/reports/tailors/
```

Use filters such as date ranges where appropriate.

## 10. API response principles

Use consistent response structures.

Successful responses should be predictable.

Errors should include:

- human-readable message
- field-level validation errors where applicable
- stable error identifiers if useful

Do not expose internal Python/Django stack traces.

## 11. Pagination

List endpoints should support pagination where datasets can grow.

## 12. Search and filtering

Search should be implemented server-side for potentially large datasets.

## 13. Authorization

Every protected endpoint must enforce backend permissions.

Frontend hiding of buttons is not security.

## 14. API documentation

Keep API documentation synchronized with implementation.

OpenAPI/Swagger may be used.

## 15. API design rule

Design APIs around business resources and meaningful operations, not around exposing database tables directly.

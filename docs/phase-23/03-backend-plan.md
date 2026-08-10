# Phase 22 — Backend Plan

## Audit
Inspect existing shop/settings models, serializers, views/viewsets, URLs, permissions and tests.

## Reuse vs Extension
Prefer the existing implementation. If `ShopDetails` already contains the required data, reuse it. Do not create another ShopSettings model.

If genuinely missing fields are required:
- Add the minimum necessary fields.
- Create a migration only when the schema changes.
- Update serializers, API behavior and tests.

## API
The API must return authoritative settings, validate writable fields server-side, enforce permissions server-side, and avoid sensitive configuration.

## Tests
Cover retrieval, valid update, invalid data, persistence, permissions, authentication and regression of existing shop-detail consumers.

## Migration checks
Run:
```text
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
```

# Phase 18 — Phone & WhatsApp Safety

## Phone Rules
1. Use the existing customer phone field.
2. Normalize only unambiguous formatting.
3. Reject malformed/unusable values.
4. Never silently guess country codes.
5. Do not store a second normalized number unless persistence is objectively required.
6. Do not log full numbers.

## WhatsApp URL Rules
- Validate destination before use.
- URL-encode message content.
- Use a fixed WhatsApp handoff base.
- Reject arbitrary URL input.
- Never claim WhatsApp delivery occurred.

## Privacy
Include only minimum necessary customer/order/payment information.

## Provider Boundary
No API token, webhook secret, provider SDK, background sender, or delivery-status implementation belongs in Phase 18.

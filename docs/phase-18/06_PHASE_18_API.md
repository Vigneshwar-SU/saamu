# Phase 18 — API Contract

## General
Communication preparation APIs are authenticated and read-only.

## Request
Identify an existing supported object and message type. Never accept arbitrary destinations, URLs, shell commands, or filesystem paths.

## Example Response
```json
{
  "success": true,
  "data": {
    "message_type": "READY_FOR_COLLECTION",
    "message": "…",
    "phone_number": "…",
    "whatsapp_url": "https://wa.me/…?text=…"
  }
}
```

The implementation may omit `whatsapp_url` if the frontend safely constructs it from validated data.

## Errors
Use:
`{success:false,error:{code,message,details?}}`

Handle unsupported message types, missing/inaccessible objects, invalid phone numbers, and malformed source data.

## HTTP Semantics
Preparation endpoints are GET-only. POST/PUT/PATCH/DELETE must not mutate communication state.
